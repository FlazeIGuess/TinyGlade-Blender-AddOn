bl_info = {
    "name": "Tiny Glade JSON Import/Export",
    "blender": (2, 80, 0),
    "category": "Import-Export",
}

import bpy
import numpy as np
import json
from mathutils import Vector
from bpy_extras.io_utils import ExportHelper, ImportHelper

# Import Operator
class ImportTinyGladeJSON(bpy.types.Operator, ImportHelper):
    """Load a Tiny Glade JSON file"""
    bl_idname = "import_scene.tiny_glade_json"
    bl_label = "Import Tiny Glade JSON"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".json"

    def execute(self, context):
        # Open and parse the JSON file
        with open(self.filepath, 'r') as f:
            data = json.load(f)
        vertex_positions = np.array([Vector(v) for v in data.get("Vertex_Position",{}).get("buffer", [])])
        vertex_normals = np.array([Vector(v) for v in data.get("Vertex_Normal",{}).get("buffer", [])])
        vertex_colors = data.get("Vertex_Color",{}).get("buffer", [])
        vertex_UV = data.get("Vertex_UV",{}).get("buffer", [])
        indices = data.get("indices",{}).get("buffer", [])
        faces = [indices[i:i+3] for i in range(0, len(indices), 3)]
        # Create a new mesh and object
        mesh = bpy.data.meshes.new("TinyGladeMesh")
        obj = bpy.data.objects.new("TinyGladeObject", mesh)
        bpy.context.collection.objects.link(obj)
        # Assign geometry to mesh
        mesh.from_pydata(vertex_positions, [], faces)
        mesh.normals_split_custom_set_from_vertices(vertex_normals)
        if not mesh.vertex_colors:
            mesh.vertex_colors.new()
        color_layer = mesh.vertex_colors.active
        # Assign colors to vertices
        for v in mesh.vertices: 
            color_layer.data[v.index].color = (*vertex_colors[v.index], 1.0)  # Add alpha value of 1.0
        mesh.update()
        return {'FINISHED'}

# Export Operator
class ExportTinyGladeJSON(bpy.types.Operator, ExportHelper):
    """Save the mesh as Tiny Glade JSON"""
    bl_idname = "export_scene.tiny_glade_json"
    bl_label = "Export Tiny Glade JSON"

    filename_ext = ".json"

    def execute(self, context):
        # Get the active mesh
        obj = context.object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Selected object is not a mesh")
            return {'CANCELLED'}

        mesh = obj.data

        # Apply object transformations (scale, rotation, translation) to vertices
        vertices = [list(obj.matrix_world @ vertex.co) for vertex in mesh.vertices]
        color_layer = []
        for v in mesh.vertex_colors.active.data:
            color_layer.append(list(v.color)[:-1])
        # Ensure mesh is triangulated
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.quads_convert_to_tris()
        bpy.ops.object.mode_set(mode='OBJECT')
        vertex_normals = [tuple(v.normal) for v in mesh.vertices]
        # Collect face indices (ensure triangles)
        faces = []
        for poly in mesh.polygons:
            faces.extend([poly.vertices[0], poly.vertices[1], poly.vertices[2]])

        # Build the JSON structure
        data = {
            'attributes': ['Vertex_Position', 'Vertex_Normal', 'Vertex_Color'],
            'indices': {'type': ['int', 1], 'buffer': faces},
            'Vertex_Position': {'type': ['float', 3], 'buffer': vertices},
            'Vertex_Normal' : {'type': ['float', 3], 'buffer': vertex_normals},
            'Vertex_Color': {'type': ['float', 3], 'buffer': color_layer},
        }

        # Save to file
        with open(self.filepath, 'w') as f:
            json.dump(data, f, indent=4)

        return {'FINISHED'}

# Add the Import/Export menus
def menu_func_import(self, context):
    self.layout.operator(ImportTinyGladeJSON.bl_idname, text="Tiny Glade JSON (.json)")

def menu_func_export(self, context):
    self.layout.operator(ExportTinyGladeJSON.bl_idname, text="Tiny Glade JSON (.json)")

# Register the add-on
def register():
    bpy.utils.register_class(ImportTinyGladeJSON)
    bpy.utils.register_class(ExportTinyGladeJSON)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ImportTinyGladeJSON)
    bpy.utils.unregister_class(ExportTinyGladeJSON)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
