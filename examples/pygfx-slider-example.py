"""
Example with which an exception could be triggered
by dragging the slider frantically for a while.

Fixed by setting fiber.component_watcher to None
in the `Collagraph.state_updated(self, fiber)` method.

Please excuse the barely working slider ;)
"""
import pygfx as gfx
from wgpu.gui.auto import run, WgpuCanvas

import collagraph as cg
from collagraph import h


class Track(cg.Component):
    track_geometry = gfx.cylinder_geometry()
    track_material = gfx.MeshPhongMaterial(color=[1, 0.5, 1])

    def render(self):
        return h(
            "Mesh",
            {
                **self.props,
                "geometry": Track.track_geometry,
                "material": Track.track_material,
            },
        )


class Scrubber(cg.Component):
    scrubber_geometry = gfx.sphere_geometry()
    scrubber_material = gfx.MeshPhongMaterial(color=[0.5, 1, 0.5])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._captured = False
        self._sphere = None
        self._mouse_pos = (0, 0)
        self.state["position"] = [0, 0, 0]

    def mouse_down(self, event):
        if not self._sphere:
            self._sphere = event.current_target
        self._sphere.set_pointer_capture(event.pointer_id)
        self._captured = True
        self._mouse_pos = event.x, event.y

    def mouse_move(self, event):
        if not self._captured:
            return

        pos = event.x, event.y
        diff = (
            pos[0] - self._mouse_pos[0],
            pos[1] - self._mouse_pos[1],
        )

        self.state["position"][2] -= diff[0] / 40
        self._mouse_pos = pos

    def mouse_up(self, event):
        self._captured = False

    def render(self):
        return h(
            "Mesh",
            {
                **self.props,
                **self.state,
                "geometry": Scrubber.scrubber_geometry,
                "material": Scrubber.scrubber_material,
                "on_pointer_down": self.mouse_down,
                "on_pointer_move": self.mouse_move,
                "on_pointer_up": self.mouse_up,
            },
        )


class Slider(cg.Component):
    def render(self):
        return h(
            "Group", self.state, h(Track, {"scale": [0.5, 0.5, 10]}), h(Scrubber, {})
        )


if __name__ == "__main__":
    canvas = WgpuCanvas(size=(600, 400))
    renderer = gfx.renderers.WgpuRenderer(canvas)

    camera = gfx.PerspectiveCamera(60, 16 / 9)
    camera.position.x = 15

    # Controls are only used to 'reset' the camera
    controls = gfx.OrbitController(camera.position.clone())
    controls.add_default_event_handlers(renderer, camera)

    gui = cg.Collagraph(
        renderer=cg.PygfxRenderer(), event_loop_type=cg.EventLoopType.QT
    )

    element = h(Slider, {})
    container = gfx.Scene()

    # Make sure the camera points to the slider
    controls.update_camera(camera)

    def animate():
        renderer.render(container, camera)

    gui.render(element, container, callback=lambda: canvas.request_draw(animate))
    run()
