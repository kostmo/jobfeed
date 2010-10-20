function getRand() {
	return Math.random() - 1/2.0;
}

// ============================================================================
function Vector2D(x, y) {
	this.x = x;
	this.y = y;

	// Operates on the current instance
	this.add = function(vec) {
		this.x += vec.x;
		this.y += vec.y;
	};

	// Operates on the current instance
	this.subtract = function(vec) {
		this.x -= vec.x;
		this.y -= vec.y;
	};


	// Operates on the current instance
	this.multiply = function(scalar) {
		this.x *= scalar;
		this.y *= scalar;
	};


	// Operates on the current instance
	this.divide = function(scalar) {
		this.x /= scalar;
		this.y /= scalar;
	};


	this.length = function() {
		return Math.sqrt(this.x*this.x + this.y*this.y);
	};

	// Operates on the current instance
	this.unitize = function() {
		var len = this.length()
		this.x /= 1.0*len;
		this.y /= 1.0*len;
	};


	// Returns a new instance
	this.dividedBy = function(scalar) {
		return new Vector2D((1.0/scalar)*this.x, (1.0/scalar)*this.y);
	};

	// Returns a new instance
	this.multipliedBy = function(scalar) {
		return new Vector2D(this.x*scalar, this.y*scalar);
	};

	// Returns a new instance
	this.subtractedBy = function(vec) {
		return new Vector2D(this.x - vec.x, this.y - vec.y);
	};

	// Returns a new instance
	this.addedBy = function(vec) {
		return new Vector2D(this.x + vec.x, this.y + vec.y);
	};
}

// ============================================================================
function Mass(m, i, fixed) {

	this.m = m;				// The mass value
	this.i = i;				// An identifier for debugging

	this.fixed = fixed;

	this.pos = new Vector2D(0, 0);		// Position in space
	this.vel = new Vector2D(0, 0);		// Velocity
	this.force = new Vector2D(0, 0);	// Force applied on this mass at an instance



	// applyForce(Vector3D force) method is used to add external force to the mass. 
	// an instance in time, several sources of force might affect the mass. The vector sum 
	// of these forces make up the net force applied to the mass at the instance.

	this.applyForce = function(f) {
		if (!this.fixed)
			this.force.add(f);	// The external force is added to the force of the mass
	};


	this.init = function() {
		this.force.x = 0;
		this.force.y = 0;
	};


	// simulate(float dt) method calculates the new velocity and new position of the mass according to change in time (dt). Here, a simulation method called
	// "The Euler Method" is used. The Euler Method is not always accurate, but it is 
	//  simple. It is suitable for most of physical simulations that we know in common 
	//  computer and video games.

	this.simulate = function(dt) {

		// XXX Mass must not be zero!
		var velocity_delta = this.force.multipliedBy(1.0*dt/this.m);

		// Change in velocity is added to the velocity.
		// The change is proportinal with the acceleration (force / m) and change in time
		this.vel.add( velocity_delta );
									
		// Change in position is added to the position.
		// Change in position is velocity times the change in time
		var position_delta = this.vel.multipliedBy(dt);
		this.pos.add( position_delta );
	};
};


// ============================================================================
// An object to represent a spring with inner friction binding two masses. The spring
// has a normal length (the length that the spring does not exert any force)
function Spring(mass1, mass2, springConstant, springLength, frictionConstant) {

	this.springConstant = springConstant;		//set the springConstant			
	this.springLength = springLength;		//The length that the spring does not exert any force
	this.frictionConstant = frictionConstant;	//A constant to be used for the inner friction of the spring

	this.mass1 = mass1;										//The first mass at one tip of the spring
	this.mass2 = mass2;										//The second mass at the other tip of the spring

	this.solve = function() {

		//vector between the two masses
		var springVector = this.mass1.pos.subtractedBy(this.mass2.pos);
		var r = springVector.length();	//distance between the two masses

		var force = new Vector2D(0, 0);																//force initially has a zero value
		if (r != 0) {	//to avoid a division by zero check if r is zero
			var multiplication_factor = (this.springLength - r) * this.springConstant / r;
			force.add( springVector.multipliedBy( multiplication_factor ) );	//the spring force is added to the force
		}

		//the friction force is added to the force
		//with this addition we obtain the net force of the spring
		var relative_velocity_vector = this.mass2.vel.subtractedBy(this.mass1.vel);
		force.add( relative_velocity_vector.multipliedBy(this.frictionConstant) );

		this.mass1.applyForce( force );			//force is applied to mass1
		this.mass2.applyForce( force.multipliedBy(-1) );	//the opposite of force is applied to mass2
	}

};


var WINDIMILL_DETECTION_MIN_REVOLUTIONS = 4;
var WINDIMILL_DETECTION_REVOLUTION_SECONDS = 1.2;

// ============================================================================
// RopeSimulation is derived from class Simulation (see Physics1.h). It simulates a rope with 
//  point-like particles binded with springs. The springs have inner friction and normal length. One tip of 
//  the rope is stabilized at a point in space called "Vector3D ropeConnectionPos". This point can be
//  moved externally by a method "void setRopeConnectionVel(Vector3D ropeConnectionVel)". RopeSimulation 
//  creates air friction and a planer surface (or ground) with a normal in +y direction. RopeSimulation 
//  implements the force applied by this surface. In the code, the surface is refered as "ground".

function RopeSimulation(
		id,
		num_masses,
		m,
		springConstant,
		springLength,
		springFrictionConstant,
		gravitation,	// Vector2D
		airFrictionConstant,
		groundRepulsionConstant,
		groundFrictionConstant,
		groundAbsorptionConstant,
		groundHeight)
{
	// Since I don't know how to do inheritance in JavaScript properly, I will reimplement all of the methods from the Simulation class.

	this.id = id;

	// My additions...
	this.current_elapsed_time = 0;
	this.gravitational_change_time = 0;



	// superclass initializer
	this.numOfMasses = num_masses;
	this.masses = new Array(this.numOfMasses);		// masses are held by pointer to pointer. (Here Mass** represents a 1 dimensional array)
	
	for (var count = 0; count < this.numOfMasses; ++count)
		this.masses[count] = new Mass(m, count, count==0);

	this.ropeConnectionPos = new Vector2D(0, 0);		//A point in space that is used to set the position of the first mass in the system (mass with index 0)
	this.ropeConnectionVel = new Vector2D(0, 0);		//a variable to move the ropeConnectionPos (by this, we can swing the rope)




	this.gravitation = gravitation;					//gravitational acceleration (gravity will be applied to all masses)
	this.original_gravitation = gravitation.multipliedBy(1);	// a backup
	
	this.current_elapsed_time = 0;
	this.gravitational_change_time = 0;

	this.airFrictionConstant = airFrictionConstant;			//a constant of air friction applied to masses
	this.groundFrictionConstant = groundFrictionConstant;		//a constant of friction applied to masses by the ground (used for the sliding of rope on the ground)
	this.groundRepulsionConstant = groundRepulsionConstant;		//a constant to represent how much the ground shall repel the masses
	this.groundAbsorptionConstant = groundAbsorptionConstant;	//a constant of absorption friction applied to masses by the ground (used for vertical collisions of the rope with the ground)
	this.groundHeight = groundHeight;				//a value to represent the y position value of the ground (the ground is a planer surface facing +y direction)


	// Note: the arm should be sampled at least once in each quadrant
	// to verify windmill behavior
	this.getWindmillActive = function() {
		return (this.windmill_quadrant_offset / 4 >= WINDIMILL_DETECTION_MIN_REVOLUTIONS);
	}
	this.last_arm_angular_position = 0;
	this.windmill_start_angular_position = 0;
	this.windmill_established_clockwise = false;
	this.previous_windmill_angular_position = 0;
	this.last_tip_relative_pos = new Vector2D(0, 0);
	this.windmill_start_time = 0;
	this.windmill_quadrant_offset = 0;


	// Initializes the rope in a force-neutral position with respect to the springs
	for (var index = 0; index < this.numOfMasses; ++index) {

		//Set x position of masses[a] with springLength distance to its neighbor
		if (this.id == 0)
			this.masses[index].pos.x = index * springLength;
		else
			this.masses[index].pos.x = -index * springLength;

		this.masses[index].pos.y = 0;				//Set y position as 0 so that it stand horizontal with respect to the ground
	}


	//Springs binding the masses (there shall be [numOfMasses - 1] of them)
	this.springs = new Array(this.numOfMasses - 1);			//create [numOfMasses - 1] pointers for springs
									//([numOfMasses - 1] springs are necessary for numOfMasses)

	for (var index = 0; index < this.numOfMasses - 1; ++index)			//to create each spring, start a loop
	{
		//Create the spring with index "a" by the mass with index "a" and another mass with index "a + 1".
		this.springs[index] = new Spring(
			this.masses[index], this.masses[index + 1],
			springConstant, springLength, springFrictionConstant);
	}


	this.init = function()								// this method will call the init() method of every mass
	{
		for (var count = 0; count < this.numOfMasses; ++count)
			this.masses[count].init();
	}


	this.getAnchorMass = function(index) {
		return this.getMass(0);
	}

	this.getTipMass = function(index) {
		return this.getMass( this.numOfMasses - 1 );
	}


	// Duplicated superclass implementation
	this.getMass = function(index) {
		if (index < 0 || index >= this.numOfMasses)
			return null;

		return this.masses[index];
	}

	// solve() is overriden because we have forces to be applied
	this.solve = function() {

		//apply force of all springs
		for (var index = 0; index < this.numOfMasses - 1; ++index)
			this.springs[index].solve();


		//Start a loop to apply forces which are common for all masses
		for (var index = 1; index < this.numOfMasses; ++index) {

			var massObject = this.masses[index];	// TODO Use this

			//The gravitational force
			massObject.applyForce( this.gravitation.multipliedBy( massObject.m ) );

			//The air friction
			massObject.applyForce( massObject.vel.multipliedBy( -this.airFrictionConstant ) );


			if (massObject.pos.y < this.groundHeight)		//Forces from the ground are applied if a mass collides with the ground
			{
				var v = massObject.vel.multipliedBy( 1 );	// get the velocity in a temporary Vector2D
				v.y = 0;					//omit the velocity component in y direction

				//The velocity in y direction is omited because we will apply a friction force to create
				//a sliding effect. Sliding is parallel to the ground. Velocity in y direction will be used
				//in the absorption effect.
				massObject.applyForce( v.multipliedBy( -this.groundFrictionConstant ) );		//ground friction force is applied

				v = massObject.vel.multipliedBy( 1 );		//get the velocity in a temporary Vector2D
				v.x = 0;						//omit the x component of the velocity

				//above, we obtained a velocity which is vertical to the ground and it will be used in
				//the absorption force

				if (v.y < 0) //let's absorb energy only when a mass collides towards the ground
					massObject.applyForce( v.multipliedBy( -this.groundAbsorptionConstant ) ); //the absorption force is applied

				//The ground shall repel a mass like a spring.
				//By "Vector3D(0, groundRepulsionConstant, 0)" we create a vector in the plane normal direction
				//with a magnitude of groundRepulsionConstant.
				//By (groundHeight - masses[a]->pos.y) we repel a mass as much as it crashes into the ground.
				var force = new Vector2D(0, this.groundRepulsionConstant).multipliedBy(this.groundHeight - massObject.pos.y);

				massObject.applyForce( force );			//The ground repulsion force is applied
			}
		}
	};



	this.simulate = function(dt) {

		this.ropeConnectionPos.add( this.ropeConnectionVel.multipliedBy( dt ) );	//iterate the positon of ropeConnectionPos

		if (this.ropeConnectionPos.y < this.groundHeight)			//ropeConnectionPos shall not go under the ground
		{
			this.ropeConnectionPos.y = this.groundHeight;
			this.ropeConnectionVel.y = 0;
		}

		this.masses[0].pos = this.ropeConnectionPos;				//mass with index "0" shall position at ropeConnectionPos
		this.masses[0].vel = this.ropeConnectionVel;				//the mass's velocity is set to be equal to ropeConnectionVel



		// A simple, two-line superclass implementation
		for (var count = 0; count < this.numOfMasses; ++count)		// We will iterate every mass
			this.masses[count].simulate(dt);				// Iterate the mass and obtain new position and new velocity




		var whip_tip = this.getTipMass();
		var tip_speed = whip_tip.vel.length();






		if (tip_speed > WHIP_SPEED_THRESHOLD) {
//		if (true) {	// FIXME

			var canvas_width = canvas.width;
			var canvas_height = canvas.height;



			// Check to see if the whip has struck any faces.
			for (var i = 0; i < flying_faces.length; ++i) {
				var face = flying_faces[i];

				var face_coords = face.getSimulationCoordinates(canvas_width, canvas_height);
				var pos_delta = whip_tip.pos.subtractedBy(face_coords);
				var tip_distance = pos_delta.length();


				if (this.id == 0)
					distance_field.value = tip_distance;


				var impact_radius = face.getRadius();

				if (this.id == 0)
					threshold_field.value = impact_radius;



				if (tip_distance < impact_radius) {
					if (!face.enraged) {
						face.setHit();
						score++;
						score_field.innerHTML = score;
						if (sound_enabled_button.checked)
							whip_sound_effect.play();
					}
				}
			}
		}



		if (true) {


			var tip_relative_pos = this.getAnchorMass().pos.subtractedBy(this.getTipMass().pos);

			// The result of atan2 will be between -PI and PI
			var current_windmill_angular_position = Math.atan2(tip_relative_pos.y, tip_relative_pos.x);
			var biased_current_angle = current_windmill_angular_position + Math.PI;
			var biased_previous_angle = this.previous_windmill_angular_position + Math.PI;

			// There are two possible arcs: the big one and the small one.
			// We assume that the smaller one is the direction of travel.
			var biased_angular_delta = biased_current_angle - biased_previous_angle;
			if (Math.abs(biased_angular_delta) > Math.PI) {
				biased_angular_delta = -biased_angular_delta;
			}

			var currently_clockwise = biased_angular_delta > 0;


			if (currently_clockwise != this.windmill_established_clockwise) {
				// The direction has changed and we must reset values.

				this.windmill_start_angular_position = 0;
				this.windmill_start_time = 0;
				this.windmill_quadrant_offset = 0;

			} else {

				// Increment the quadrant offset if we have entered a new quadrant.
				if ((this.last_tip_relative_pos.x > 0) != (tip_relative_pos.x > 0)
					|| (this.last_tip_relative_pos.y > 0) != (tip_relative_pos.y > 0)) {

					this.windmill_quadrant_offset++;
				}
			}

			if (this.id == 0)
				quadrant_counter_field.innerHTML = this.windmill_quadrant_offset;

			this.windmill_established_clockwise = currently_clockwise;


			this.last_tip_relative_pos = tip_relative_pos;
			this.previous_windmill_angular_position = current_windmill_angular_position;
		}


	}

	//the method to set ropeConnectionVel (accepts a Vector2D)
	this.setRopeConnectionVel = function(ropeConnectionVel) {
		this.ropeConnectionVel = ropeConnectionVel;
	}


	this.operate = function(dt, main_loop_iteration_number) {

		// TODO Periodically apply random gravity?
		this.current_elapsed_time += dt;
//		printf("Current elapsed time: %0.3f\n", current_elapsed_time);

		if (false) {
//		if (current_elapsed_time >= gravitational_change_time) {
			this.gravitational_change_time = this.current_elapsed_time + 0.5;	// Every two seconds, change the gravity.

			var random_vector = new Vector2D(getRand(), getRand());	// Genearate a random direction vector, with values between -1 and 1
			random_vector.unitize();
			random_vector.multiply(original_gravitation.length()/8.0);

			this.gravitation = this.random_vector;
		}


		// Full superclass implementation:
		this.init();				// Step 1: reset forces to zero
		this.solve();				// Step 2: apply forces
		this.simulate(dt);
	}

	// Draw the arms as connected line segments
	this.drawToCanvas = function(ctx) {

		ctx.beginPath();

		var pos = this.getAnchorMass().pos;
		ctx.moveTo(pos.x, pos.y);

		for (var index = 1; index < this.numOfMasses; ++index) {
			var pos = this.getMass(index).pos;
			ctx.lineTo(pos.x, pos.y);
		}
		ctx.lineJoin = "round";

		ctx.moveTo(pos.x + ctx.lineWidth, pos.y);
		ctx.arc(pos.x, pos.y, ctx.lineWidth, 0, 2*Math.PI, false);


		var tip_speed = this.getTipMass().vel.length();
		if (this.id == 0) {
			speed_field.value = tip_speed;
		}

		if (tip_speed > WHIP_SPEED_THRESHOLD) {
			ctx.save();
				ctx.lineWidth *= 3;
				ctx.strokeStyle = "#0F0";
				ctx.stroke();
			ctx.restore()
		}


		ctx.stroke();
	}
};
