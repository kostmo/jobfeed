#!/usr/bin/env python

'''Splits and reassembles the image without the middle.'''

# ==============================================================================
def make_serrations_points(tooth_amplitude, tooth_count):
	tooth_serrations = []
	tooth_spacing = original_width/tooth_count
	for i in range(tooth_count):
		peak = (i*tooth_spacing, -tooth_amplitude/2)
		tooth_serrations.append(peak)
		trough = (int((i + 0.5)*tooth_spacing), tooth_amplitude/2)
		tooth_serrations.append(trough)

	# Add one last peak on the right edge:
	last_peak = (original_width - 1, -tooth_amplitude/2)
	tooth_serrations.append(last_peak)
	return tooth_serrations

# ==============================================================================
def points_offset_vertical(points, offset):
	return [(x, y + offset) for x, y in points]

# ==============================================================================
def make_serrations_mask(tooth_serrations, original_width, vertical_edge):

	tooth_mask_polygon = tooth_serrations[:]
	# Add upper left corner
	tooth_mask_polygon.append( (original_width - 1, vertical_edge) )
	# Add upper right corner
	tooth_mask_polygon.append( (0, vertical_edge) )

	alpha_mask = Image.new('L', source.size, 0)
	alpha_mask_draw = ImageDraw.Draw(alpha_mask)
	alpha_mask_draw.polygon(tooth_mask_polygon, fill=255)
	
	return alpha_mask

# =============================================================================
def ellipsize_image(source, upper_cutoff_y, lower_cutoff_y, gap_height, tooth_amplitude, tooth_count):

	from PIL import Image, ImageDraw
	from dropshadow import dropShadow

	original_width, original_height = source.size

	base_serrations = make_serrations_points(tooth_amplitude, tooth_count)
	upper_tooth_serrations = points_offset_vertical(base_serrations, upper_cutoff_y)
	lower_tooth_serrations = points_offset_vertical(base_serrations, lower_cutoff_y)


	upper_alpha_mask = make_serrations_mask(upper_tooth_serrations, original_width, 0)
#	upper_alpha_mask.save("upper_tooth_mask.png")

	lower_alpha_mask = make_serrations_mask(lower_tooth_serrations, original_width, original_height - 1)
#	lower_alpha_mask.save("lower_tooth_mask.png")


	top_cropped_region = source.crop(upper_alpha_mask.getbbox())
#	top_cropped_region.save("top.png")

	bottom_cropped_region = source.crop(lower_alpha_mask.getbbox())
#	bottom_cropped_region.save("bottom.png")


	bottom_offset = top_cropped_region.size[1] + gap_height - tooth_amplitude
	composited = Image.new('RGBA', (original_width, bottom_offset + bottom_cropped_region.size[1]))
	composited.paste(top_cropped_region, (0, 0), upper_alpha_mask.crop( upper_alpha_mask.getbbox() ))
	composited.paste(bottom_cropped_region, (0, bottom_offset), lower_alpha_mask.crop( lower_alpha_mask.getbbox() ))
#	composited.save("foo.png")

	shadowed = dropShadow(composited)
	return shadowed

# =============================================================================
if __name__ == '__main__':

	from PIL import Image, ImageDraw
	source = Image.open("../../screenshots/nuke.png")

	original_width, original_height = source.size
	upper_cutoff_y = original_height/3
	lower_cutoff_y = 7*original_height/8

	gap_height = 25
	tooth_amplitude = 30
	tooth_count = 6

	ellipsized = ellipsize_image(source, upper_cutoff_y, lower_cutoff_y, gap_height, tooth_amplitude, tooth_count)
	ellipsized.save("output.png")

