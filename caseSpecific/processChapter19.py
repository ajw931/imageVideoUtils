import addTextBlockToImage
import createGif

## Add text to the images in the main ch19 folder
#baseDir = "D:\\Data\\MyRenders\\Jen\\Jen_story\\Scene_5_game_show\\ch19_round1"
#args = {}
#args['image_dir'] = baseDir
#args['text_dir'] = baseDir + "\\text"
#args['output_dir'] = baseDir + "\\withText"
#args['extension'] = "png"
#addTextBlockToImage.addTextBlockToImage(args)

## Add text to the images in the tube-shrink folder
#baseDir = "D:\\Data\\MyRenders\\Jen\\Jen_story\\Scene_5_game_show\\ch19_round1\\tube-shrink"
#args = {}
#args['image_dir'] = baseDir
#args['text_dir'] = baseDir + "\\text"
#args['output_dir'] = baseDir + "\\withText"
#args['extension'] = "png"
#args['mode'] = 'pattern'
#addTextBlockToImage.addTextBlockToImage(args)

## Add text to the images in the tube-7 folder
#baseDir = "D:\\Data\\MyRenders\\Jen\\Jen_story\\Scene_5_game_show\\ch19_round1\\tube-7"
#args = {}
#args['image_dir'] = baseDir
#args['text_dir'] = baseDir + "\\text"
#args['output_dir'] = baseDir + "\\withText"
#args['extension'] = "jpg"
#args['mode'] = 'pattern'
#addTextBlockToImage.addTextBlockToImage(args)

# Call this AFTER running batch-image-resize.sh.  I haven't yet integrated that into here.
# Create tube-shrink gif
createGif.create_animated_gif(baseDir="D:\\Data\\MyRenders\\Jen\\Jen_story_RESIZED_2880x2160\\Scene_5_game_show\\ch19_round1\\tube-shrink\\withText",
                              baseName='tube-shrink',
                              delay=120,
                              extension='jpg')
# Create tube-shrink gif
createGif.create_animated_gif(baseDir="D:\\Data\\MyRenders\\Jen\\Jen_story_RESIZED_1600x1200\\Scene_5_game_show\\ch19_round1\\tube-7\\withText",
                              baseName='tube-7',
                              delay=10,
                              extension='jpg')