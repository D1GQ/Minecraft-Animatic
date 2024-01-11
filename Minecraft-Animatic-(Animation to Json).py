import bpy
import json
import math
from decimal import Decimal, ROUND_HALF_UP

# Define supported format versions
FORMAT_VERSIONS = [
    "1.8.0", "1.10.0", "1.11.0", "1.12.0", "1.13.0", "1.14.0", "1.16.0", "1.16.100", "1.16.200",
    "1.16.210", "1.16.220", "1.17.0", "1.17.10", "1.17.20", "1.17.30", "1.17.40", "1.18.0", "1.18.10",
    "1.18.20", "1.18.30", "1.19.0", "1.19.10", "1.19.20", "1.19.30", "1.19.40", "1.19.50", "1.19.60",
    "1.19.70", "1.19.80", "1.20.0", "1.20.10", "1.20.20", "1.20.30", "1.20.40",
]

# Inside the export_minecraft_animation function, modify the rotation and position data accordingly
def export_minecraft_animation(context, filepath, anim_id, loop, override, anim_time_update, blend_weight, start_delay, loop_delay, format_version, invert_rotation_axes, invert_position_axes, export_armature):
    # Ensure the file has a .json extension
    if not filepath.lower().endswith('.json'):
        filepath += '.json'

    # Map loop options
    loop_mapping = {"Play Once": False, "Loop": True, "Hold On Last Frame": "hold_on_last_frame"}

    # Convert animation length from frames to seconds
    anim_length_seconds = (context.scene.frame_end - context.scene.frame_start) / context.scene.render.fps

    # Initialize the data structure
    export_data = {
        "format_version": format_version,
        "animations": {
            anim_id: {
                "loop": loop_mapping[loop],
                "animation_length": round(anim_length_seconds, 5),
                "override_previous_animation": override,
                **{key: value for key, value in {
                    "anim_time_update": anim_time_update if anim_time_update != "0.0" else None,
                    "blend_weight": blend_weight if blend_weight != "0.0" else None,
                    "start_delay": start_delay if start_delay != "0.0" else None,
                    "loop_delay": loop_delay if loop_delay != "0.0" else None
                }.items() if value},
                "bones": {}
            }
        }
    }

    # Initialize variables outside the loop
    transformed_position = None
    transformed_scale = None

    # Iterate through selected objects
    for obj in bpy.context.selected_objects:
        if obj.type == 'ARMATURE' and export_armature:
            armature = obj.data

            for bone in armature.bones:
                # Check if bone has animation data
                if obj.animation_data and obj.animation_data.action:
                    bone_data = {
                        "rotation": {},
                        "position": {},
                        "scale": {}
                    }

                    # Iterate through keyframes in the animation
                    keyframes = set()

                    for fc in obj.animation_data.action.fcurves:
                        if fc.data_path in [f'pose.bones["{bone.name}"].location',
                                            f'pose.bones["{bone.name}"].rotation_quaternion',
                                            f'pose.bones["{bone.name}"].rotation_euler',
                                            f'pose.bones["{bone.name}"].scale']:
                            keyframes.update(int(k.co.x) for k in fc.keyframe_points)

                    # If there are no keyframes for the current bone, skip processing
                    if not keyframes:
                        print(f"Skipping bone {bone.name} in armature {obj.name} as it has no animation data.")
                        continue

                    # Sort keyframes in ascending order
                    sorted_keyframes = sorted(keyframes)

                    for frame in sorted_keyframes:
                        bpy.context.scene.frame_set(frame)

                        # Rotation data
                        if bpy.data.objects[obj.name].pose.bones[bone.name].rotation_mode == 'XYZ':
                            rotation_data_euler = bpy.data.objects[obj.name].pose.bones[bone.name].rotation_euler
                        else:
                            rotation_quaternion = bpy.data.objects[obj.name].pose.bones[bone.name].rotation_quaternion
                            rotation_data_euler = rotation_quaternion.to_euler()

                        # Convert to degrees and invert specific axes if needed, rounding to one decimal place
                        rotation_data = [
                            float(Decimal(math.degrees(angle)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)) if axis not in invert_rotation_axes 
                            else float(Decimal(-math.degrees(angle)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
                            for axis, angle in enumerate(rotation_data_euler)
                        ]

                        if not hasattr(bpy.data.objects[obj.name].pose.bones[bone.name], 'rotation_quaternion'):
                            # Swap Y and Z values for XYZ rotation
                            rotation_data = [rotation_data[0], rotation_data[2], rotation_data[1]]

                        # Invert X Y & Z and Rotation data
                        rotation_data[0] = -rotation_data[0]
                        rotation_data[1] = -rotation_data[1]
                        rotation_data[2] = -rotation_data[2]
                        
                        # If invert options are true in export menu
                        if invert_rotation_axes[2]:
                            rotation_data[2] = -rotation_data[2]

                        # Multiply rotation values by the rotation multiplier
                        rotation_data = [angle * ROTATION_MULTIPLIER for angle in rotation_data]

                        # Add the modified rotation data to bone_data
                        bone_data["rotation"][round(frame / bpy.context.scene.render.fps, 5)] = rotation_data

                        # Original position data
                        original_position = bpy.data.objects[obj.name].pose.bones[bone.name].location

                        # Multiply position values by the multiplier
                        transformed_position = [coord * POSITION_MULTIPLIER for coord in original_position]

                        # Invert Y and Z components of position_data
                        transformed_position[2] = -transformed_position[2]
                        
                        # If invert options are true in export menu
                        if invert_position_axes[0]:
                            transformed_position[0] = -transformed_position[0]
                        if invert_position_axes[1]:
                            transformed_position[1] = -transformed_position[1]
                        if invert_position_axes[2]:
                            transformed_position[2] = -transformed_position[2]

                        # Add the modified position data to bone_data["position"]
                        bone_data["position"][round(frame / bpy.context.scene.render.fps, 5)] = transformed_position

                        # Scale data
                        scale_data = bpy.data.objects[obj.name].pose.bones[bone.name].scale

                        # Multiply scale values by the scale multiplier
                        transformed_scale = [coord * SCALE_MULTIPLIER for coord in scale_data]

                        bone_data["scale"][round(frame / bpy.context.scene.render.fps, 5)] = transformed_scale

                    # Add bone data to export_data
                    if bone.name not in export_data["animations"][anim_id]["bones"]:
                        export_data["animations"][anim_id]["bones"][bone.name] = {}

                    export_data["animations"][anim_id]["bones"][bone.name].update(bone_data)

                else:
                    # Skip bones with no animation data
                    print(f"Skipping bone {bone.name} in armature {obj.name} as it has no animation data.")
                    
        elif obj.animation_data and obj.animation_data.action:
            # Check if object has animation data
            bone_data = {
                "rotation": {},
                "position": {},
                "scale": {}
            }

            # Iterate through keyframes in the animation
            keyframes = set()
            for fc in obj.animation_data.action.fcurves:
                keyframes.update(int(k.co.x) for k in fc.keyframe_points)

            # Sort keyframes in ascending order
            sorted_keyframes = sorted(keyframes)

            for frame in sorted_keyframes:
                bpy.context.scene.frame_set(frame)

                # Check if the rotation mode is XYZ
                if obj.rotation_mode == 'XYZ':
                    # Use raw Euler angles without conversions
                    rotation_data = [round(math.degrees(angle), 5) for angle in obj.rotation_euler]
                    rotation_data[0] = -rotation_data[0]
                else:
                    # Convert to degrees and invert specific axes if needed, rounding to one decimal place
                    rotation_data = [
                        float(Decimal(math.degrees(angle)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)) if axis not in invert_rotation_axes 
                        else float(Decimal(-math.degrees(angle)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
                        for axis, angle in enumerate(quaternion_to_euler_xyz(obj.rotation_quaternion))
                    ]

                # Check if the rotation data is non-zero before inverting
                if any(invert_rotation_axes):
                    rotation_data = [(-angle if invert_rotation_axes[axis] else angle) for axis, angle in enumerate(rotation_data)]

                # Multiply rotation values by the rotation multiplier
                rotation_data = [angle * ROTATION_MULTIPLIER for angle in rotation_data]
                
                # Invert Rotation X & Z
                rotation_data[0] = -rotation_data[0]
                rotation_data[2] = -rotation_data[2]
                
                # Swap Y and Z values for rotation
                rotation_data = [rotation_data[0], rotation_data[2], rotation_data[1]]

                # Add the modified rotation data to bone_data
                bone_data["rotation"][round(frame / context.scene.render.fps, 5)] = rotation_data.copy()

                # Original position data
                original_position = [round(coord, 5) for coord in obj.location]

                # Swap Y and Z values for position
                transformed_position = [original_position[0], original_position[2], original_position[1]]
                
                # Multiply position values by the multiplier
                transformed_position = [coord * OBJ_POSITION_MULTIPLIER for coord in transformed_position]

                # Position data
                bone_data["position"][round(frame / context.scene.render.fps, 5)] = transformed_position.copy()

                # Scale data
                scale_data = [round(scale, 5) for scale in obj.scale]
                bone_data["scale"][round(frame / context.scene.render.fps, 5)] = scale_data.copy()

                # Swap Y and Z values for scale
                transformed_scale = [scale_data[0], scale_data[2], scale_data[1]]
                bone_data["scale"][round(frame / context.scene.render.fps, 5)] = transformed_scale.copy()

                # Multiply scale values by the scale multiplier
                transformed_scale = [coord * SCALE_MULTIPLIER for coord in transformed_scale]
                bone_data["scale"][round(frame / context.scene.render.fps, 5)] = transformed_scale.copy()

            # Add bone data to export_data
            export_data["animations"][anim_id]["bones"][obj.name] = bone_data
        else:
            # Skip objects with no animation data
            print(f"Skipping {obj.name} as it has no animation data.")

    # Export to JSON
    with open(filepath, 'w') as file:
        json.dump(export_data, file, indent=4)

    return {'FINISHED'}


# Define the export operator
class ExportMinecraftAnimation(bpy.types.Operator):
    bl_idname = "export.minecraft_animation"
    bl_label = "Export"
    bl_options = {'PRESET'}
    filepath: bpy.props.StringProperty(subtype="FILE_PATH", options={'HIDDEN'})
    
    format_version: bpy.props.EnumProperty(name="Format Version", items=[(ver, ver, "") for ver in FORMAT_VERSIONS], default="1.8.0")
    anim_id: bpy.props.StringProperty(name="Animation ID", default="animation.blender.exported")
    export_armature: bpy.props.BoolProperty(name="Export Armature", default=False)
    
    loop_options = [("Play Once", "Play Once", ""), ("Loop", "Loop", ""), ("Hold On Last Frame", "Hold On Last Frame", "")]
    loop: bpy.props.EnumProperty(name="Loop", items=loop_options, default="Play Once")
    override: bpy.props.BoolProperty(name="Override Previous Animation", default=False)
    loop_delay: bpy.props.StringProperty(name="Loop Delay", default="")
    start_delay: bpy.props.StringProperty(name="Start Delay", default="")
    blend_weight: bpy.props.StringProperty(name="Blend Weight", default="")
    anim_time_update: bpy.props.StringProperty(name="Animation Time Update", default="")

    invert_rotation_X: bpy.props.BoolProperty(name="Invert Rotation X", default=False)
    invert_rotation_Y: bpy.props.BoolProperty(name="Invert Rotation Y", default=False)
    invert_rotation_Z: bpy.props.BoolProperty(name="Invert Rotation Z", default=False)

    invert_position_X: bpy.props.BoolProperty(name="Invert Position X", default=False)
    invert_position_Y: bpy.props.BoolProperty(name="Invert Position Y", default=False)
    invert_position_Z: bpy.props.BoolProperty(name="Invert Position Z", default=False)
    
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )

    def execute(self, context):
        invert_rotation_axes = [self.invert_rotation_X, self.invert_rotation_Y, self.invert_rotation_Z]
        invert_position_axes = [self.invert_position_X, self.invert_position_Y, self.invert_position_Z]

        return export_minecraft_animation(
            context, self.filepath, self.anim_id, self.loop, self.override,
            self.anim_time_update, self.blend_weight, self.start_delay,
            self.loop_delay, self.format_version, invert_rotation_axes,
            invert_position_axes, self.export_armature
        )

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        self.filepath = "animation.blender.json"
        return {'RUNNING_MODAL'}

# Register the operator
def menu_func_export(self, context):
    self.layout.operator(ExportMinecraftAnimation.bl_idname, text="Export Minecraft Animation (.json)")

def register():
    bpy.utils.register_class(ExportMinecraftAnimation)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ExportMinecraftAnimation)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
