
import bpy
import blf
class DrawingClass:
    def __init__(self, context, prop):
        self.prop = prop
        self.handle = bpy.types.SpaceView3D.draw_handler_add(
                   self.draw_text_callback,(context,),
                   'WINDOW', 'POST_PIXEL')

    def draw_text_callback(self, context):
        font_id = 0  # XXX, need to find out how best to get this.

        # draw some text
        blf.position(font_id, 15, 50, 0)
        blf.size(font_id, 20, 72)
        blf.draw(font_id, "%s %s" % (context.scene.name, self.prop))

    def remove_handle(self):
         bpy.types.SpaceView3D.draw_handler_remove(self.handle, 'WINDOW')


def clear_hud():
    dns = bpy.app.driver_namespace
    hud = dns.get("hud")
    hud.remove_handle()

def print(data, delay=1):
    context = bpy.context             
    dns = bpy.app.driver_namespace
    dns["hud"] = DrawingClass(context, data)
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1) 
    bpy.app.timers.register(clear_hud, first_interval=delay)