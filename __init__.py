# ##### BEGIN GPL LICENSE BLOCK #####
#
#  Copyright (C) 2018 Amir Shehata
#  http://www.openmovie.com
#  amir.shehata@gmail.com

#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import traceback, json, os, fnmatch
from bpy.props import IntProperty, StringProperty, EnumProperty

bl_info = {
    "name": "YAKM",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "location": "View3D > UI > YAKM",
    "author": "Amir Shehata <amir.shehata@gmail.com>",
    "description": "Yet Another Keyframe Manager",
    "category": "provides helpful utilities for managing key frames"
}

def load_stored_actions_list():
    actions = []
    try:
        directory = os.path.dirname(bpy.data.filepath)
    except:
        return actions
    i = 0
    if not os.path.isdir(directory):
        return actions
    for fname in os.listdir(directory):
        if fnmatch.fnmatch(fname, 'yakm_*.json'):
            entry = os.path.splitext(fname)[0]
            actions.append((os.path.join(directory,fname), entry, entry, '', i))
            i += 1
    return actions

def read_stored_action(path):
    data = {}
    if not os.path.isfile(path):
        return data
    with open(path, 'r') as f:
        data = json.load(f)
    return data

class YAKM_OT_refresh_actions(bpy.types.Operator):
    bl_idname = "yakm.refresh_actions"
    bl_label = "Refresh"
    bl_description = "Refresh the list of user actions"

    def execute(self, context):
        cxt = bpy.context
        scn = cxt.scene
        bpy.types.Scene.yakm_action_dropdown = EnumProperty(
            description="List of existing actions stored by the user",
            items=load_stored_actions_list(),
            name='Stored Actions')
        return {'FINISHED'}

class YAKM_OT_apply_action(bpy.types.Operator):
    bl_idname = "yakm.apply_action"
    bl_label = "Apply"
    bl_description = "Apply selected actions on selected bones"

    def ShowMessageBox(self, message = "", title = "Error", icon = 'ERROR'):
        def draw(self, context):
            self.layout.label(text=message)
        bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

    def execute(self, context):
        cxt = bpy.context
        scn = cxt.scene

        data = read_stored_action(scn.yakm_action_dropdown)

        for bone in bpy.context.selected_pose_bones:
            bname = bone.name
            if not bname in data:
                continue
            try:
                bpose = bpy.context.object.pose.bones[bname]
                delta = 0
                first = True
                frame_current = scn.frame_current
                for kf, v in data[bname].items():
                    if not first:
                        delta = int(float(kf)) - prevf
                    first = False
                    insf = frame_current + delta
                    frame_current = insf
                    prevf = int(float(kf))
                    bpose.rotation_quaternion[0] = data[bname][kf]['rotation_quaternion'][0]
                    bpose.rotation_quaternion[1] = data[bname][kf]['rotation_quaternion'][1]
                    bpose.rotation_quaternion[2] = data[bname][kf]['rotation_quaternion'][2]
                    bpose.rotation_quaternion[3] = data[bname][kf]['rotation_quaternion'][3]
                    bpose.location[0] = data[bname][kf]['location'][0]
                    bpose.location[1] = data[bname][kf]['location'][1]
                    bpose.location[2] = data[bname][kf]['location'][2]
                    bpose.scale[0] = data[bname][kf]['scale'][0]
                    bpose.scale[1] = data[bname][kf]['scale'][1]
                    bpose.scale[2] = data[bname][kf]['scale'][2]
                    bpose.keyframe_insert('rotation_quaternion', frame=insf)
                    bpose.keyframe_insert('location', frame=insf)
                    bpose.keyframe_insert('scale', frame=insf)
                    print("insert bone %s insf = %d" % (bname, insf))
            except Exception as e:
                print(e)
                continue

        return {'FINISHED'}

class YAKM_OT_store_action(bpy.types.Operator):
    bl_idname = "yakm.store_action"
    bl_label = "Store"
    bl_description = "Store the frame range specified as an action"

    def ShowMessageBox(self, message = "", title = "Error", icon = 'ERROR'):
        def draw(self, context):
            self.layout.label(text=message)
        bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

    def execute(self, context):
        cxt = bpy.context
        scn = cxt.scene
        bfile = bpy.data.filepath
        store_action = {}
        # get all the keyframes
        if not scn.yakm_action_name:
            self.ShowMessageBox(message="Please specify the action to use from the action editor")
            return {'FINISHED'}
        try:
            action = bpy.data.actions[scn.yakm_action_name]
        except:
            self.ShowMessageBox(message="%s not found" % scn.yakm_action_name)
            return {'FINISHED'}
        keyframe_list = []
        for fcu in action.fcurves:
            for keyframe in fcu.keyframe_points:
                if keyframe.co[0] not in keyframe_list:
                    if int(keyframe.co[0]) < int(scn.yakm_start_frame) or \
                       int(keyframe.co[0]) > int(scn.yakm_end_frame):
                        continue
                    keyframe_list.append(keyframe.co[0])

        selected_bones = bpy.context.selected_pose_bones
        frame_current = scn.frame_current
        for bone in bpy.context.selected_pose_bones:
            bname = bone.name
            store_action[bname] = {}
            try:
                for kf in keyframe_list:
                    bpose = bpy.context.object.pose.bones[bname]
                    scn.frame_set(kf)
                    store_action[bname][kf] = {}
                    store_action[bname][kf]['rotation_quaternion'] = list(bpose.rotation_quaternion)
                    store_action[bname][kf]['location'] = list(bpose.location)
                    store_action[bname][kf]['scale'] = list(bpose.scale)
            except:
                continue
        scn.frame_set(frame_current)
        store_action_fpath = os.path.join(os.path.dirname(bfile),
                             os.path.splitext('yakm_'+os.path.basename(bfile))[0]+"_"+scn.yakm_store_action_name+".json")
        with open(store_action_fpath, 'w') as f:
            json.dump(store_action, f, indent=2, ensure_ascii=False)

        # update the list
        bpy.types.Scene.yakm_action_dropdown = EnumProperty(
            description="List of existing actions stored by the user",
            items=load_stored_actions_list(),
            name='Stored Actions')

        return {'FINISHED'}

class YAKM_OT_delete_keyframes(bpy.types.Operator):
    bl_idname = "yakm.delete_keyframes"
    bl_label = "Delete"
    bl_description = "Delete key frames on selected bone"

    def execute(self, context):
        selected_bones = bpy.context.selected_pose_bones
        for bone in bpy.context.selected_pose_bones:
            bname = bone.name
            try:
                for i in range(bpy.context.scene.yakm_start_frame,
                               bpy.context.scene.yakm_end_frame):
                    bpy.context.object.pose.bones[bname].keyframe_delete('rotation_euler', frame=i)
                    bpy.context.object.pose.bones[bname].keyframe_delete('rotation_quaternion', frame=i)
                    bpy.context.object.pose.bones[bname].keyframe_delete('location', frame=i)
                    bpy.context.object.pose.bones[bname].keyframe_delete('scale', frame=i)
            except:
                continue
        return {'FINISHED'}


class YAKM_PT_main(bpy.types.Panel):
    bl_label = "Keyframe Manager"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'YAKM'

    def draw(self, context):
        scn = context.scene
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="Frame Range")
        col = layout.column(align=True)
        row = col.row(align=False)
        row.prop(scn, "yakm_start_frame", text="")
        row.prop(scn, "yakm_end_frame", text="")
        col = layout.column(align=True)
        col.label(text="Remove keyframes in range")
        col.operator('yakm.delete_keyframes', icon='TRASH')
        col = layout.column(align=True)
        col.label(text="Store keyframes in range")
        col.prop(scn, "yakm_action_name", text="Src")
        col.prop(scn, "yakm_store_action_name", text="Dest")
        col.operator('yakm.store_action', icon='FILE')
        col = layout.column(align=True)
        col.label(text="Apply Actions")
        col.prop(scn, "yakm_action_dropdown", text="")
        row = col.row(align=False)
        row.operator('yakm.refresh_actions', icon='FILE_REFRESH')
        row.operator('yakm.apply_action', icon='KEY_HLT')

def register():
    bpy.utils.register_class(YAKM_OT_refresh_actions)
    bpy.utils.register_class(YAKM_OT_apply_action)
    bpy.utils.register_class(YAKM_OT_store_action)
    bpy.utils.register_class(YAKM_OT_delete_keyframes)
    bpy.utils.register_class(YAKM_PT_main)
    bpy.types.Scene.yakm_start_frame = IntProperty(
        name="Start Frame",
        default = 1,
        description='Animation start frame')
    bpy.types.Scene.yakm_end_frame = IntProperty(
        name="End Frame",
        default = 2,
        description='Animation end frame')
    bpy.types.Scene.yakm_store_action_name = StringProperty(
        name="Destination Action Name",
        subtype='FILE_NAME',
        default='',
        description='Name of the action to store the animation data into.\n\
This is stored as a file co-located with the blender file')
    bpy.types.Scene.yakm_action_name = StringProperty(
        name="Source Action Name",
        subtype='FILE_NAME',
        default='',
        description='Action name from the blender action editor.\n\
This is the source of the animation data')
    bpy.types.Scene.yakm_action_dropdown = EnumProperty(
        description="List of existing actions stored by the user",
        items=load_stored_actions_list(),
        name='Stored Actions')

def unregister():
    bpy.utils.unregister_class(YAKM_PT_main)
    bpy.utils.register_class(YAKM_OT_delete_keyframes)

if __name__ == "__main__":
    register()
