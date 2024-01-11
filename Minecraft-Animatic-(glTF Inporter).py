import bpy
import math
from bpy_extras.io_utils import ImportHelper

class MinecraftGltfImportOperator(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.minecraft_gltf"
    bl_label = "Minecraft glTF (.gltf)"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".gltf"
    filter_glob: bpy.props.StringProperty(
        default="*.gltf;*.glb",
        options={'HIDDEN'},
    )

    def execute(self, context):
        filepath = self.filepath
        bpy.ops.import_scene.gltf(filepath=filepath, filter_glob="*.gltf;*.glb", loglevel=30, import_pack_images=True, import_shading='NORMALS')

        # Special code to run after importing the file
        print("Running special code after importing Minecraft .gltf")
        
        # Clear all selected objects
        bpy.ops.object.select_all(action='DESELECT')

        # Iterate through all objects and select the one with the keyword "Node_"
        selected_empty = None
        for obj in bpy.data.objects:
            if "Node_" in obj.name:
                obj.select_set(True)
                selected_empty = obj
                bpy.context.view_layer.objects.active = obj

        # Check if a valid empty is selected
        if selected_empty:
            # Rotate the selected empty's Z rotation to 180 degrees
            quat_rot = selected_empty.rotation_quaternion
            euler_rot = quat_rot.to_euler('XYZ')
            euler_rot[2] = math.pi  # 180 degrees in radians
            selected_empty.rotation_quaternion = euler_rot.to_quaternion()

            # Print a message to confirm the rotation
            print(f"Rotated {selected_empty.name}'s Z rotation to 180 degrees.")

            # Select all empties directly parented to the selected empty
            bpy.ops.object.select_grouped(type='CHILDREN_RECURSIVE')

            # Set empties size and shapes
            size, display_type = 0.05, 'CUBE'

            for obj in bpy.context.selected_objects:
                if obj.type == 'EMPTY':
                    obj.empty_display_size, obj.empty_display_type = size, display_type
                    obj.show_in_front = True

            size_key, display_type_key = 0.3, 'SPHERE'
            keyword = 'root'

            for obj in bpy.context.selected_objects:
                if obj.type == 'EMPTY' and keyword.lower() in obj.name.lower():
                    obj.empty_display_size, obj.empty_display_type = size_key, display_type_key
                    obj.show_in_front = True

            # Iterate through all objects and select the one with the keyword "Node_"
            selected_empty = None
            for obj in bpy.data.objects:
                if "Node_" in obj.name:
                    obj.select_set(True)
                    selected_empty = obj
                    bpy.context.view_layer.objects.active = obj

            # Deselect objects that are not empties
            bpy.ops.object.select_by_type(type='EMPTY', extend=False)

            # Set rotation mode
            for obj in bpy.context.selected_objects:
                obj.rotation_mode = 'XYZ'

            # Apply rotation to selected empties
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

            # Set transforms to deltas
            bpy.ops.object.transforms_to_deltas(mode='ALL')


        # Clear all selected objects
        bpy.ops.object.select_all(action='DESELECT')

        # Iterate through all objects and select the one with the keyword "Node_"
        selected_empty = None
        for obj in bpy.data.objects:
            if "Node_" in obj.name:
                obj.select_set(True)
                selected_empty = obj
                bpy.context.view_layer.objects.active = obj

        # Get the selected objects in the current scene
        selected_objects = bpy.context.selected_objects

        # Loop through selected objects and delete them
        for obj in selected_objects:
            bpy.data.objects.remove(obj, do_unlink=True)

        # Update the scene after deleting objects
        bpy.context.view_layer.update()

        # Clear all selected objects
        bpy.ops.object.select_all(action='DESELECT')

        # Return a result for the operator
        return {'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(MinecraftGltfImportOperator.bl_idname, text="Minecraft glTF Model (.gib/gltf)")

def register():
    bpy.utils.register_class(MinecraftGltfImportOperator)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(MinecraftGltfImportOperator)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
