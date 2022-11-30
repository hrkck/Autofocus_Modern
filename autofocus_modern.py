'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

import bpy
import bl_math

from bpy.props import (
    FloatProperty,
    BoolProperty,
    CollectionProperty,
    StringProperty,
    IntProperty
    )
from bpy.types import (
    Panel,
    PropertyGroup,
    )

from bpy.app.handlers import persistent
from mathutils import Vector

import time

last_time = time.time()
elapsed = 0.0

lerp_locations = {}
        
    
def find_cam(scn, af):
    for obj in scn.objects:
        if(obj.type=='CAMERA' and obj.data.autofocus != None
        and obj.data.autofocus == af):
            return obj
    return None
        
def set_enabled(self, value):
    self["enabled"] = value
    scn = bpy.context.scene
    cam = bpy.context.object # find_cam(scn, self)
    if value:
        uid = cam.name + str(time.time())
        cam.data.autofocus.uid = uid
        a_cam = scn.autofocus_properties.active_cameras.add()
        a_cam.camera = cam
        a_cam.name = uid # cam.name
        
        if uid not in lerp_locations:
            lerp_locations[uid] = [0, True, 0, 1]
        
        
        reset_clock()
    else:
        i = scn.autofocus_properties.active_cameras.find(cam.data.autofocus.uid)
        print(f"number found {i}")
        scn.autofocus_properties.active_cameras.remove(i)
        # cam.data.autofocus.smooth = False
        try:
            del lerp_locations[cam.data.autofocus.uid]
        except KeyError:
            pass
    
def get_enabled(self):
    if self.get("enabled") == None:
        return False
    else:
        return self["enabled"]
    
def set_smooth_enabled(self, value):
    self["smooth"] = value
    
def get_smooth_enabled(self):
    if self.get("smooth") == None:
        return False
    else:
        return self["smooth"]
    
def set_smooth_offset(self, value):
    self["smooth_offset"] = value
    
def get_smooth_offset(self):
    if self.get("smooth_offset") == None:
        return 0
    else:
        return self["smooth_offset"]
    
def set_timer_enabled(self, value):
    self["enabled"] = value
    reset_clock()
    
def get_timer_enabled(self):
    if self.get("enabled") == None:
        return False
    else:
        return self["enabled"]
    
class AutoFocus_Properties(PropertyGroup):
    enabled: BoolProperty(
        name="Enabled",
        default=False,
        description="Enable auto focus for this camera.",
        get=get_enabled,
        set=set_enabled
        )
    smooth: BoolProperty(
        name="Smoothing",
        default=False,
        description="Enable smoothing for auto focus using slow parent.",
        get=get_smooth_enabled,
        set=set_smooth_enabled
        )
    smooth_offset: IntProperty(
        name="Offset",
        min=1,
        default=1,
        description="Higher values mean slower focusing. 24 means smooth focus will be complete in 1 second",
        get=get_smooth_offset,
        set=set_smooth_offset
        )
    uid: StringProperty(
        name="UID",
        default="",
        description="Unique Identifier"
        )
        
class AutoFocus_Active_Camera(PropertyGroup):
    name: bpy.props.StringProperty(name="cameraName", 
        default="", 
        description="Active Camera Name")
    camera: bpy.props.PointerProperty(type=bpy.types.Object)
        
class AutoFocus_Scene_Properties(PropertyGroup):
    active_cameras: CollectionProperty(
        type=AutoFocus_Active_Camera
    )
    rate_enabled: BoolProperty(
        name="Timer",
        default=True,
        description="Enable timer between AutoFocus updates. (Improves performance)",
        get=get_timer_enabled,
        set=set_timer_enabled
        )
    rate_seconds: FloatProperty(
        name="Seconds",
        default=0.5,
        description="The rate in seconds between AutoFocus updates. (Disabled = update on every scene update)"
        )
        
class AutoFocus_Panel(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'
    bl_label = "Auto Focus"
    
    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type == 'CAMERA' and context.object.data
    
    def draw_header(self, context):
        af = context.object.data.autofocus
        self.layout.prop(af, "enabled", text="")
    
    def draw(self, context):
        af = context.object.data.autofocus
        layout = self.layout
        
        row = layout.row()
        row.active = af.enabled
        row.prop(af, "smooth")
        row = layout.row()
        row.enabled = af.smooth
        row.prop(af, "smooth_offset")
        
        split = layout.split()
        split.prop(context.scene.autofocus_properties, "rate_enabled")
        split.prop(context.scene.autofocus_properties, "rate_seconds")
    
@persistent
def scene_update(scn, depsgraph):
    if scn.autofocus_properties.rate_enabled and not check_clock(scn):
        return
    
    for n, cam in enumerate(bpy.context.scene.autofocus_properties.active_cameras):

        try:
            if cam.camera.type != "CAMERA": continue
            cam = cam.camera
        except:
            scn.autofocus_properties.active_cameras.remove(n)
        
        
        cam_matrix = cam.matrix_world
        org = cam_matrix @ Vector((0.0, 0.0, 0.0))
        dst = cam_matrix @ Vector((0.0, 0.0, -100.0))
        dir = dst - org

        result, location, normal, index, object, matrix = scn.ray_cast(depsgraph, org, dir)

        if result:
            current_dist = cam.data.dof.focus_distance
            new_dist_vector = cam.location - location
            new_dist = new_dist_vector.length

            if cam.data.autofocus.enabled:
                if cam.data.autofocus.smooth:
                    global lerp_locations # get lerp locs for smooth
                    
                    if cam.data.autofocus.uid not in lerp_locations:
                        lerp_locations[cam.data.autofocus.uid] = [0, True, 0, 1]
            
                    if isDistAlmostEqual(current_dist, new_dist):
                        lerp_locations[cam.data.autofocus.uid] = [new_dist, True, current_dist, 1]
                    else:
                        lerp_locations[cam.data.autofocus.uid] = [new_dist, False, lerp_locations[cam.data.autofocus.uid][2], lerp_locations[cam.data.autofocus.uid][3]]
                else:
                    print("setting dist")
                    cam.data.dof.focus_distance = new_dist
            

@persistent
def run_24_times():        
    if bpy.context.scene.autofocus_properties.rate_enabled and not check_clock(bpy.context.scene):
        return 0.041
    
    # print(len(bpy.context.scene.autofocus_properties.active_cameras))
    for n, cam in enumerate(bpy.context.scene.autofocus_properties.active_cameras):
        if cam.camera.type != "CAMERA": continue
        cam = cam.camera
        # try:
        #     # print(n)
        #     # cam = c.camera
        #     # print(cam.data.autofocus.uid)
        # except Exception:
        #     print('cam not found')
        #     continue
        
        global lerp_locations
        print(lerp_locations)
        if cam.data.autofocus.uid not in lerp_locations or not cam.data.autofocus.smooth: 
            # print('continuing')
            continue
        # if not any(lerp_locations[cam.data.autofocus.uid]): continue
        
        offset = cam.data.autofocus.smooth_offset
        
        if lerp_locations[cam.data.autofocus.uid][3] >= offset:
            lerp_locations[cam.data.autofocus.uid][3] = 0
        else:
            if lerp_locations[cam.data.autofocus.uid][3] == None:
                lerp_locations[cam.data.autofocus.uid][3] = 1
            else:
                lerp_locations[cam.data.autofocus.uid][3] += 1
        
            
        foc_dist = cam.data.dof.focus_distance
        
        # print(lerp_locations[cam.data.autofocus.uid])
        lerp_dest = lerp_locations[cam.data.autofocus.uid][0]
        isDestSame = lerp_locations[cam.data.autofocus.uid][1]
        current_dist = foc_dist
        
        if isDestSame:
            continue
        
        # if current smooth foc_dist not equal lerp_dest, 
        # then get initial_loc and reset global frame counter
        if not abs(foc_dist - lerp_dest) < 0.01 and isDestSame:
            lerp_locations[cam.data.autofocus.uid][3] = 1
    
        step_destination = bl_math.lerp(current_dist, lerp_dest, lerp_locations[cam.data.autofocus.uid][3] / offset) 

        cam.data.dof.focus_distance = step_destination
    return 0.041


def isPosEqual(pos1, pos2):
    return pos1.x == pos2.x and pos1.y == pos2.y and pos1.z == pos2.z

def isDistEqual(dist1, dist2):
    return dist1 == dist2

def isDistAlmostEqual(dist1, dist2):
    return abs(dist1 - dist2) < 0.01 

def check_clock(scn):
    global last_time
    global elapsed
    cur_time = time.time()
    
    elapsed += cur_time - last_time
    last_time = cur_time
    
    if elapsed >= scn.autofocus_properties.rate_seconds:
        elapsed = 0.0
        return True
    
    return False

def reset_clock():
    global last_time
    global elapsed
    last_time = time.time()
    elapsed = 0.0
        
