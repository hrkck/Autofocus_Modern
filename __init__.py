# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "Autofocus_Modern",
    "author" : "Hakki R Kucuk, Leigh Harborne, ",
    "description" : "Sets camera to autofocus on nearest surface.",
    "blender" : (3, 3, 1),
    "version" : (0, 4, 0),
    "doc_url": "https://shardsofred.gumroad.com/",
    "warning" : "Smooth function does not work yet, contibutions are welcome!",
    "location": "Properties > Data ",
    "category": "Object",
}

import bpy

import math

from bpy.props import (
    FloatProperty,
    BoolProperty,
    PointerProperty,
    CollectionProperty,
    StringProperty,
    )
from bpy.types import (
    Panel,
    PropertyGroup,
    )

from bpy.app.handlers import persistent
from mathutils import Vector

import time

from . autofocus_modern import *

def register():
    bpy.utils.register_class(AutoFocus_Panel)
    bpy.utils.register_class(AutoFocus_Properties)
    bpy.utils.register_class(AutoFocus_Active_Camera)
    bpy.utils.register_class(AutoFocus_Scene_Properties)
    bpy.types.Camera.autofocus = PointerProperty(
                                    type=AutoFocus_Properties
                                    )
    bpy.types.Scene.autofocus_properties = PointerProperty(
                                    type=AutoFocus_Scene_Properties
                                    )
    bpy.app.handlers.depsgraph_update_post.append(scene_update)
    

def unregister():    
    bpy.utils.unregister_class(AutoFocus_Panel)
    bpy.utils.unregister_class(AutoFocus_Properties)
    bpy.utils.unregister_class(AutoFocus_Active_Camera)
    bpy.utils.unregister_class(AutoFocus_Scene_Properties)
    bpy.app.handlers.depsgraph_update_post.remove(scene_update)
    del bpy.types.Camera.autofocus
    del bpy.types.Scene.autofocus_properties

if __name__ == "__main__":
    register()
    pass