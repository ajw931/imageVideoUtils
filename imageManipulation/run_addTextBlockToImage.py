import addTextBlockToImage

#baseDir = "D:\\Data\\MyRenders\\Jen\\Jen_story\\Scene_5_game_show\\ch19_round1"
#args = {}
#args['image_dir'] = baseDir
#args['text_dir'] = baseDir + "\\text"
#args['output_dir'] = baseDir + "\\withText"
#args['extension'] = "png"

baseDir = "D:\\Data\\MyRenders\\Jen\\Jen_story\\Scene_5_game_show\\ch19_round1\\tube-shrink"
args = {}
args['image_dir'] = baseDir
args['text_dir'] = baseDir + "\\text"
args['output_dir'] = baseDir + "\\withText"
args['extension'] = "png"
args['mode'] = 'pattern'

addTextBlockToImage.addTextBlockToImage(args)