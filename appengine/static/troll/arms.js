var canvas;  
var ctx;
var timestep = 0.005;
var trollface;
var last_click_pos;
var scale_size;
var mouse_button_down = false;
var GRAVITATIONAL_CONSTANT = 9.81;
var next_spawn_time = new Date();
var AVERAGE_SPAWN_SECONDS = 5;

var WHIP_SPEED_THRESHOLD = 8;
var NOMINAL_ARM_LENGTH = 1.8;
var arm_mass_count = 30;



//var MAX_FLYERS = 1;	// FIXME
var MAX_FLYERS = 5;
var score = 0;


var flying_faces = [];
var speed_field;
var distance_field;
var threshold_field;
var score_field;
var sound_enabled_button;
var quadrant_counter_field;




var last_recorded_date;
var iteration_count;
var ropeSimulations;
var keys_pressed;
var started_simulation;
var which_click_button = 1;

var guitar_image_loaded = false;

var whip_sound_effect = new Audio("whip.ogg");
var guitar_img = new Image();
guitar_img.src = "guitar.png";
guitar_img.onload = function() {
	guitar_image_loaded = true;
};

function MaleFace() {
//	this.happy = "http://ragecomic.appspot.com/packs/happy/images/Happy.png";
	this.happy = "Happy.png";
//	this.rage = "http://ragecomic.appspot.com/packs/rage/images/OriginalRage.png";
	this.rage = "OriginalRage.png";
}

function FemaleFace() {
//	this.happy = "http://ragecomic.appspot.com/packs/happy/images/FemaleHappy.png";
	this.happy = "FemaleHappy.png";
//	this.rage = "http://ragecomic.appspot.com/packs/rage/images/FemaleRage.png";
	this.rage = "FemaleRage.png";
}


function getFaceImage(male, enraged) {
	var face = male ? new MaleFace() : new FemaleFace();
	var img = new Image();
	img.src = enraged ? face.rage : face.happy;
	return img;
}


function FlyingFace() {

	this.BASE_PERIOD = 8.0;	// Seconds to traverse distance

	this.angle = Math.random()*2*Math.PI;
	this.progress = 0;	// A fractional distance from the center

	this.period = this.BASE_PERIOD*(Math.random() + 1/2.0);	// +/- 50%
	this.rotational_frequency = (Math.random() - 0.5)*5;
	this.male = Math.random() > 0.5;
	this.enraged = false;

	this.img = getFaceImage(this.male, this.enraged);

	this.setHit = function() {
		this.enraged = true;
		this.rotational_frequency *= 2;
		this.img = getFaceImage(this.male, this.enraged);
	}



	// The scaled distance from canvas center to any corner
	this.getMaxDistance = function(width, height) {
		return new Vector2D(width, height).length()/2.0;
	}

	this.draw = function(ctx, width, height) {

		var max_distance = this.getMaxDistance(width, height);

		ctx.save();
			ctx.rotate(this.angle);
			ctx.translate(max_distance*this.progress, 0);
			ctx.rotate(this.progress * 2*Math.PI * this.rotational_frequency);

			var scaled_w = this.img.width*this.progress;
			var scaled_h = this.img.height*this.progress;

			var offset_h = -scaled_w/2.0;
			var offset_v = -scaled_h/2.0;

			try {
				// Note: Sometimes Firefox produces a weird Javascript error on this line.
				ctx.drawImage(this.img, offset_h, offset_v, scaled_w, scaled_h);
			} catch (e) {

			}

		ctx.restore();
	}


	this.simulate = function(dt) {	// dt must be given in seconds
		this.progress += dt/this.period;
//		this.progress = 0.1;	// FIXME
	}

	this.isFinished = function() {
		return this.progress > 1;
	}


	this.getSimulationCoordinates = function(width, height) {
		var max_distance = this.getMaxDistance(width, height);
		var scaled_distance = max_distance/scale_size;
		var vector = new Vector2D( Math.cos(this.angle), -Math.sin(this.angle) )
		vector.multiply(scaled_distance);
		return vector;
	}


	this.getRadius = function() {
		return this.progress * Math.max(this.img.width, this.img.height)/scale_size;
	}
}




function KeysPressed() {

	this.first_click = false;

	this.reset = function() {
		this.left = false;
		this.up = false;
		this.right = false;
		this.down = false;
	}

	this.reset();

	this.any = function() {
		return this.left || this.up || this.right || this.down;
	}
}



function sceneInit() {



	keys_pressed = new KeysPressed();
	started_simulation = false;

	last_recorded_date = new Date();
	iteration_count = 0;

	ropeSimulations = new Array(2);
	for (var i=0; i<ropeSimulations.length; i++)
		ropeSimulations[i] = new RopeSimulation(
			i,
			arm_mass_count,		// 3 Particles (Masses)
			0.05,				// Each Particle Has A Weight Of 50 Grams
	//		10000.0,			// springConstant In The Rope
			1000.0,				// springConstant In The Rope
			NOMINAL_ARM_LENGTH/(arm_mass_count - 1),	// Normal Length Of Springs In The Rope
			0.2,				// Spring Inner Friction Constant
			new Vector2D(0, -GRAVITATIONAL_CONSTANT),		// Gravitational Acceleration
			0.02,				// Air Friction Constant
			100.0,				// Ground Repel Constant
			0.2,				// Ground Slide Friction Constant
			2.0,				// Ground Absoption Constant
//			-1.5);				// Ground height
			-10);				// Ground height

	canvas = document.getElementById("canvas");
	ctx = canvas.getContext("2d");
	trollface = new Image();


	speed_field = document.getElementById("speed_field");
	distance_field = document.getElementById("distance_field");
	threshold_field = document.getElementById("threshold_field");
	score_field = document.getElementById("score_field");
	sound_enabled_button = document.getElementById("sound_enabled_button");
	quadrant_counter_field = document.getElementById("quadrant_counter_field");
	

//	flying_faces.push( new FlyingFace() );	// FIXME
//	trollface.src = 'http://i.imgur.com/VO1NP.jpg';
	trollface.src = 'http://i.imgur.com/r6WI2.png';

	setInterval(mainIteration, 40);
}


function mainIteration() {

	var current_date = new Date();
	var elapsed_millis = current_date.getTime() - last_recorded_date.getTime();
	last_recorded_date = current_date;

	if (!started_simulation) {
		if (keys_pressed.any() || keys_pressed.first_click) {
			started_simulation = true;
			keys_pressed.reset();
		}
	} else {
		updateSimulation( elapsed_millis, iteration_count, timestep);




		var now = new Date();
		if (now.getTime() >= next_spawn_time.getTime()) {

			next_spawn_time = new Date( now.getTime() + Math.random()*AVERAGE_SPAWN_SECONDS*1000 );

			// TODO Maybe should use an Exponential random variable with lambda = 1/AVERAGE_SPAWN_SECONDS;


			if (flying_faces.length < MAX_FLYERS) {
//				flying_faces.push( new FlyingFace() );	// FIXME
				flying_faces.push( new FlyingFace() );
			}

		}

		iteration_count++;
	}



	scale_size = Math.min(canvas.width, canvas.height)/5.0;
	draw(canvas.width, canvas.height);
}





function transformClickCoords(click_point) {

	var center_point = new Vector2D(canvas.width, canvas.height);
	center_point.divide(2.0);

	var centered_click_point = click_point.subtractedBy(center_point);
	centered_click_point.divide(scale_size);

	return centered_click_point;
}



function updateSimulation(milliseconds, iteration_count, maxPossible_dt) {


	// Get direction from anchor point to click point
	if (last_click_pos) {
		var gravity_vector = transformClickCoords(last_click_pos);
		gravity_vector.y *= -1;
		gravity_vector.unitize();
		gravity_vector.multiply(GRAVITATIONAL_CONSTANT);

		ropeSimulations[which_click_button].gravitation = gravity_vector;
	}

	var ropeConnectionVel = new Vector2D(0, 0);	// Create A Temporary Vector2D

	if (keys_pressed.left)
		ropeConnectionVel.x -= 3.0;						// Add Velocity In -X Direction

	if (keys_pressed.right)
		ropeConnectionVel.x += 3.0;						// Add Velocity In +X Direction

	if (keys_pressed.up)
		ropeConnectionVel.y += 3.0;						// Add Velocity In +Y Direction

	if (keys_pressed.down)
		ropeConnectionVel.y -= 3.0;						// Add Velocity In -Y Direction


	keys_pressed.reset();


	for (var i=0; i<ropeSimulations.length; i++)
		ropeSimulations[i].setRopeConnectionVel(ropeConnectionVel);		// Set The Obtained ropeConnectionVel In The Simulation

	var dt = milliseconds / 1000.0;	// Converts Milliseconds To Seconds

	for (var i=0; i<flying_faces.length; i++) {
		var face = flying_faces[i];
		face.simulate(dt);
	}

	function isBigEnough(element, index, array) {
	  return !element.isFinished();
	}

	flying_faces = flying_faces.filter(isBigEnough);



	// Calculate Number Of Iterations To Be Made At This Update Depending On maxPossible_dt And dt
  	var numOfIterations = Math.floor((dt / maxPossible_dt) + 1);			
	if (numOfIterations != 0)		// Avoid Division By Zero
		dt = dt / numOfIterations;	// dt Should Be Updated According To numOfIterations

	for (var i=0; i<ropeSimulations.length; i++)
		for (var a = 0; a < numOfIterations; ++a)	// We Need To Iterate Simulations "numOfIterations" Times
			ropeSimulations[i].operate(dt, iteration_count);
}



function drawGravityRing(pointer_pos) {

	var transformed_click_center = transformClickCoords(pointer_pos);
	transformed_click_center.y *= -1;

	// Point of button click
	if (false) {
		ctx.beginPath();
		ctx.arc(transformed_click_center.x, transformed_click_center.y, 5*ctx.lineWidth, 0, 2*Math.PI, false);
		ctx.closePath();
		ctx.stroke();
	}


	var ring_thickness = 20;

	// Gravity indicator ring
	var gravity_indicator_radius = 2.5;
	ctx.save();
		ctx.lineWidth *= ring_thickness;

		if (which_click_button == 0)
			ctx.strokeStyle = "rgba(255, 0, 0, 0.25)";
		else
			ctx.strokeStyle = "rgba(0, 0, 255, 0.25)";

		ctx.beginPath();
		ctx.arc(0, 0, gravity_indicator_radius, 0, 2*Math.PI, false);
		ctx.closePath();
		ctx.stroke();
	ctx.restore();


	ctx.save();
//		var grav_delta = transformed_click_center.subtractedBy(ropeSimulations[0].getAnchorMass().pos);
		var grav_delta = transformed_click_center;
		ctx.rotate(Math.atan2(grav_delta.y, grav_delta.x));
		ctx.translate(gravity_indicator_radius, 0);
		var triangle_overscale = 1.3;
		ctx.scale(triangle_overscale, triangle_overscale);

		var size = ctx.lineWidth * ring_thickness;
		// Draw triangle
		ctx.beginPath();
		ctx.moveTo(-size/2.0, 0);
		ctx.lineTo(size/2.0, size/2.0);
		ctx.lineTo(size/2.0, -size/2.0);
		ctx.closePath();

		ctx.lineJoin = "round";
		ctx.stroke();
		ctx.fillStyle = "rgba(0, 0, 0, 0.25)";
		ctx.fill();
	ctx.restore();
}


function drawCenteredImage(ctx, img) {
	ctx.drawImage( img, -img.width/2, -img.height/2);
}

function drawBody(ctx, width, height) {

	var face_height = trollface.height

	// The head
	ctx.drawImage(trollface, -trollface.width/2, -face_height);

	var torso_height = face_height/2;

	// Stick body/legs
	ctx.beginPath();
	ctx.moveTo(0, 0);
	ctx.lineTo(0, torso_height);

	ctx.moveTo(-torso_height, 2*torso_height);
	ctx.lineTo(0, torso_height);
	ctx.lineTo(torso_height, 2*torso_height);
	ctx.stroke();

	// The guitar
	if (guitar_image_loaded) {

		var windmilling = false;
		for (var i=0; i<ropeSimulations.length; i++) {
			if (ropeSimulations[i].getWindmillActive()) {
				windmilling = true;
				break;
			}
		}


		if (windmilling) {

			ctx.save();
				ctx.translate(0, torso_height);
				drawCenteredImage(ctx, guitar_img);
			ctx.restore();
		}
	}
}


function drawArms(ctx, width, height) {
	for (var i=0; i<ropeSimulations.length; i++) {
		if (i == 0) ctx.strokeStyle = "#F00";
		else ctx.strokeStyle = "#00F";

		ropeSimulations[i].drawToCanvas(ctx);
	}
}

function drawFaces(ctx, width, height) {
	for (var i=0; i<flying_faces.length; i++) {
		var face = flying_faces[i];

		face.draw(ctx, width, height);
	}
}

function draw(width, height) {

	ctx.clearRect(0, 0, width, height)
	ctx.lineWidth = 4;

	ctx.beginPath();
	ctx.rect(0, 0, width, height);
	ctx.closePath();
	ctx.stroke();

	ctx.save();
		ctx.translate(width/2.0, height/2.0);

		drawBody(ctx)


		ctx.save();
			ctx.scale(scale_size, -scale_size);
			ctx.lineWidth /= scale_size;


			if (last_click_pos)
				drawGravityRing(last_click_pos);

			drawArms(ctx, width, height);

		ctx.restore();

		drawFaces(ctx, width, height);


	ctx.restore();
}

