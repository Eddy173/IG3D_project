import bpy

def apply_lens(focus_distance=10, num_layers=6, max_blur=70, focal_length=0.03, f_stop=2.8):
    aperture = focal_length / f_stop
    scene = bpy.context.scene
    scene.use_nodes = True
    bpy.context.view_layer.use_pass_z = True
    tree = scene.node_tree
    tree.nodes.clear()

    rl = tree.nodes.new('CompositorNodeRLayers')
    normalize = tree.nodes.new('CompositorNodeNormalize')
    tree.links.new(rl.outputs['Depth'], normalize.inputs[0])

    min_depth = 0.1
    max_depth = 50.0
    depth_range = max_depth - min_depth
    previous_layer = None

    for i in range(num_layers):
        layer_min = i / num_layers
        layer_max = (i + 1) / num_layers
        norm_center = (layer_min + layer_max) / 2.0
        real_center_depth = norm_center * depth_range + min_depth
        coc_radius = abs(real_center_depth - focus_distance) * aperture * max_blur
        coc_radius = min(coc_radius, max_blur)

        greater = tree.nodes.new('CompositorNodeMath')
        greater.operation = 'GREATER_THAN'
        greater.inputs[1].default_value = layer_min

        less = tree.nodes.new('CompositorNodeMath')
        less.operation = 'LESS_THAN'
        less.inputs[1].default_value = layer_max

        mask = tree.nodes.new('CompositorNodeMath')
        mask.operation = 'MULTIPLY'
        tree.links.new(normalize.outputs[0], greater.inputs[0])
        tree.links.new(normalize.outputs[0], less.inputs[0])
        tree.links.new(greater.outputs[0], mask.inputs[0])
        tree.links.new(less.outputs[0], mask.inputs[1])

        set_alpha = tree.nodes.new('CompositorNodeSetAlpha')
        tree.links.new(rl.outputs['Image'], set_alpha.inputs['Image'])
        tree.links.new(mask.outputs[0], set_alpha.inputs['Alpha'])

        sep = tree.nodes.new('CompositorNodeSeparateColor')
        tree.links.new(set_alpha.outputs[0], sep.inputs[0])

        red_translate = tree.nodes.new('CompositorNodeTranslate')
        red_translate.inputs['X'].default_value = 10
        tree.links.new(sep.outputs['Red'], red_translate.inputs[0])

        blue_translate = tree.nodes.new('CompositorNodeTranslate')
        blue_translate.inputs['X'].default_value = -10
        tree.links.new(sep.outputs['Blue'], blue_translate.inputs[0])

        combine = tree.nodes.new('CompositorNodeCombineColor')
        tree.links.new(red_translate.outputs[0], combine.inputs['Red'])
        tree.links.new(sep.outputs['Green'], combine.inputs['Green'])
        tree.links.new(blue_translate.outputs[0], combine.inputs['Blue'])

        alpha_mix = tree.nodes.new('CompositorNodeSetAlpha')
        tree.links.new(combine.outputs[0], alpha_mix.inputs['Image'])
        tree.links.new(mask.outputs[0], alpha_mix.inputs['Alpha'])

        premul = tree.nodes.new('CompositorNodePremulKey')
        tree.links.new(alpha_mix.outputs[0], premul.inputs[0])

        blur = tree.nodes.new('CompositorNodeBlur')
        blur.filter_type = 'GAUSS'
        blur.use_relative = False
        blur.size_x = int(coc_radius)
        blur.size_y = int(coc_radius)
        tree.links.new(premul.outputs[0], blur.inputs[0])
       
        if previous_layer is None:
            previous_layer = blur
        else:
            over = tree.nodes.new('CompositorNodeAlphaOver')
            over.use_premultiply = True
            tree.links.new(previous_layer.outputs[0], over.inputs[1])
            tree.links.new(blur.outputs[0], over.inputs[2])
            previous_layer = over
           
    final = tree.nodes.new('CompositorNodeAlphaOver')
    final.use_premultiply = True
    tree.links.new(rl.outputs['Image'], final.inputs[1])
    tree.links.new(previous_layer.outputs[0], final.inputs[2])

    comp = tree.nodes.new('CompositorNodeComposite')
    viewer = tree.nodes.new('CompositorNodeViewer')
    tree.links.new(final.outputs[0], comp.inputs[0])
    tree.links.new(final.outputs[0], viewer.inputs[0])

def render_code():
    apply_lens()
    scene=bpy.context.scene
    scene.render.image_settings.file_format='FFMPEG'
    scene.render.ffmpeg.format= 'MPEG4'
    scene.render.ffmpeg.codec= 'H264'
    scene.render.ffmpeg.constant_rate_factor='MEDIUM'
    scene.render.ffmpeg.ffmpeg_preset='GOOD'
    scene.render.ffmpeg.video_bitrate = 6000
    scene.render.filepath= "//project_final_vid/video.mp4"
    scene.render.use_compositing=True
    scene.render.use_sequencer=False
    bpy.ops.render.render(animation=True)

render_code()