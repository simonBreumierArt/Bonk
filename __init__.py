import os
import sys
import bpy
import numpy as np
from mathutils import Vector
from bpy.app.handlers import persistent
from bpy.props import (
    FloatProperty, IntProperty,
)

modules_names = ['LODStripUtilities']
modules_full_names = {}
for current_module_name in modules_names:
	modules_full_names[current_module_name] = ('{}.{}'.format(__name__, current_module_name))

import importlib

for current_module_full_name in modules_full_names.values():
	if current_module_full_name in sys.modules:
		importlib.reload(sys.modules[current_module_full_name])
	else:
		globals()[current_module_full_name] = importlib.import_module(current_module_full_name)
		setattr(globals()[current_module_full_name], 'modulesNames', modules_full_names)

def register():
	for current_module_name in modules_full_names.values():
		if current_module_name in sys.modules:
			if hasattr(sys.modules[current_module_name], 'register'):
				sys.modules[current_module_name].register()

def unregister():
	for current_module_name in modules_full_names.values():
		if current_module_name in sys.modules:
			if hasattr(sys.modules[current_module_name], 'unregister'):
				sys.modules[current_module_name].unregister()

from . import LODStripUtilities

bl_info = {
    "name": "HideExport",
    "author": "Simon Breumier",
    "version": (0,0,0),
    "blender": (4,3,2),
    "description": "Apply all modifiers, transforms, join all objects and perform basic cube UV for all object in a collection to export to Hide as an fbx"
}
   
from bpy.props import (
    StringProperty,
    PointerProperty,
    BoolProperty,
)

@persistent 
def MakeLOD1Only(creaseOffset, eps, subdiv, red_param): 
    htd = bpy.context.scene.htd
    
    if 'stripToogle' in htd.keys():
        doStrips = htd['stripToogle']
    else:
        doStrips = True

    col_name = bpy.context.collection.name
    if doStrips:
        LODStripUtilities.createLOD1(col_name, eps=eps, subdiv=subdiv, CreaseOffset=creaseOffset, red_param=red_param)
    else:
        for obj in bpy.data.collections[col_name].all_objects: 
            if "MainBevel" in obj.modifiers:
                obj.modifiers["MainBevel"].show_viewport = False
            if "MainBevel.001" in obj.modifiers:
                        obj.modifiers["MainBevel.001"].show_viewport = False
            if "MainBevel.002" in obj.modifiers:
                        obj.modifiers["MainBevel.002"].show_viewport = False

        bpy.context.collection.name = bpy.context.collection.name + "_LOD1"
                
        LODStripUtilities.HideExport_fbx(False, red_param)
        bpy.ops.object.modifier_add_node_group(asset_library_type='ESSENTIALS', asset_library_identifier="", relative_asset_identifier="geometry_nodes\\smooth_by_angle.blend\\NodeTree\\Smooth by Angle")
        bpy.ops.object.modifier_add(type='TRIANGULATE')
        bpy.context.object.modifiers["Triangulate"].keep_custom_normals = True
        bpy.ops.mesh.customdata_custom_splitnormals_clear()

        col_name = bpy.context.collection.name
        for obj in bpy.data.collections[col_name].all_objects: 
            if "MainBevel" in obj.modifiers:
                obj.modifiers["MainBevel"].show_viewport = True
            if "MainBevel.001" in obj.modifiers:
                obj.modifiers["MainBevel.001"].show_viewport = True
            if "MainBevel.002" in obj.modifiers:
                obj.modifiers["MainBevel.002"].show_viewport = True
    
        bpy.context.collection.name = bpy.context.collection.name[:-5]

@persistent 
def MakeQuickLOD(creaseOffset, eps, subdiv, red_param): 
    col_name = bpy.context.collection.name

    bpy.context.collection.name = bpy.context.collection.name + "_LOD0"
    LODStripUtilities.HideExport_fbx(True)
    bpy.context.collection.name = bpy.context.collection.name[:-5]
    bpy.ops.object.select_all(action='DESELECT')

    MakeLOD1Only(creaseOffset, eps, subdiv, red_param)

    htd = bpy.context.scene.htd
    numLods = 2
    if 'lodNum' in htd.keys():
        numLods = int(htd['lodNum'])

    numLods = max(2, min(numLods,9))

    decimateRatio = np.linspace(1.0 / numLods, 1.0 - 1.0 / numLods, numLods)
    for i in range(2, numLods):
         bpy.ops.object.select_all(action='DESELECT')
         bpy.context.scene.objects[col_name + "_LOD1"].select_set(True)
         bpy.context.view_layer.objects.active = bpy.context.scene.objects[col_name + "_LOD1"]
         bpy.ops.object.duplicate()
         bpy.context.selected_objects[0].name = col_name + "_LOD" + str(i)
         bpy.ops.object.modifier_add(type='DECIMATE')
         bpy.context.object.modifiers["Decimate"].ratio = 1 - decimateRatio[i]
         bpy.ops.object.modifier_move_to_index(modifier="Decimate", index=0)






         

def RemoveIntFaces():
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bpy.ops.mesh.select_interior_faces()
    bpy.ops.mesh.delete(type='FACE')
    bpy.ops.object.mode_set(mode="OBJECT")


@persistent 
def CleanDecalUV():  
    for obj in bpy.context.selected_objects:
        try:
            #obj.data.uv_layers.data.uv_layer_stencil.name = 'UVMap'
            obj.data.uv_layers[0].name = "UVMap"
            
            if ("Decal UVs" in obj.data.uv_layers):
                obj.data.uv_layers.remove(obj.data.uv_layers["Decal UVs"])
        except:
            continue

@persistent 
def HideBools():
    
    tested = False
    for objActu in bpy.context.view_layer.objects:
        if(objActu.display_type == 'WIRE'):
            if not(tested):
                tested = True
                visval = not(objActu.hide_get())
            objActu.hide_set(visval)
            objActu.hide_viewport = visval

def AddMainBevel():
    if not("Smooth by Angle" in bpy.context.object.modifiers):
        bpy.ops.object.shade_auto_smooth()
    bpy.ops.object.modifier_add(type='BEVEL', use_selected_objects=True)
    bpy.context.object.modifiers[-2].name = "MainBevel"
    bpy.context.object.modifiers["MainBevel"].width = 0.015   
    bpy.context.object.modifiers["MainBevel"].harden_normals = True
    
    modifName = "Smooth by Angle"
    for elem in bpy.context.object.modifiers:
        if "Smooth by Angle" in elem.name:
            modifName = elem.name
    i=0
    bpy.context.object.modifiers[modifName].use_pin_to_last = False
    for elem in bpy.context.object.modifiers:
        if bpy.context.object.modifiers[i].name != "MainBevel":
            i+=1
        else:
            break
    bpy.ops.object.modifier_move_to_index(modifier=modifName, index=i)


def AddWeightBevel(segments=3):
    bpy.ops.object.modifier_add(type='BEVEL', use_selected_objects=True)
    bpy.context.object.modifiers[-1].name = "WeightBevel"
    bpy.context.object.modifiers["WeightBevel"].limit_method = 'WEIGHT'
    bpy.context.object.modifiers["WeightBevel"].segments = segments
    
def MakeCrevice(width):
    htd = bpy.context.scene.htd
    creviceThick = width

    obj = bpy.context.selected_objects[0]

    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.inset(thickness=creviceThick, depth=0)
    bpy.ops.mesh.delete(type='FACE')
    bpy.ops.mesh.select_all(action='INVERT')

    LODStripUtilities.MultiAutoCreviceUV()



def ReduceCylinder():
    bpy.ops.mesh.select_nth()
    bpy.ops.mesh.loop_multi_select(ring=False)
    bpy.ops.mesh.dissolve_edges()


def removeEmptyMaterials():
    newMesh = bpy.context.selected_objects[0]
    mat_list = [m.name for m in bpy.data.materials]
    object_mats = newMesh.material_slots

    mode = bpy.context.active_object.mode
    bpy.ops.object.mode_set(mode='OBJECT')
    i=0
    for matActu in object_mats:
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='DESELECT')
        matActuName = matActu.name
        newMesh.active_material_index = i
        bpy.ops.object.material_slot_select()
        bpy.ops.object.editmode_toggle()
        selectedVerts = [v for v in bpy.context.active_object.data.vertices if v.select]
        if len(selectedVerts) == 0:
            bpy.ops.object.material_slot_remove()
        i+=1
    bpy.ops.object.mode_set(mode=mode)

def IncreaseCylinder():
    bpy.ops.mesh.loop_multi_select(ring=False)
    bpy.ops.mesh.bevel(offset_type='PERCENT', offset=0, offset_pct=25, affect='EDGES')

class MESH_OT_HideExport(bpy.types.Operator):
    bl_idname = "mesh.hide_export"
    bl_label = "Export to Hide"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        bpy.context.collection.name = bpy.context.collection.name + "_LOD0"
        LODStripUtilities.HideExport_fbx(True)
        bpy.context.collection.name = bpy.context.collection.name[:-5]
        
        return {"FINISHED"}

class MESH_OT_MakeQuickLOD(bpy.types.Operator):
    bl_idname = "mesh.make_quicklod"
    bl_label = "Make 3 LODs reday for export"
    bl_options = {"REGISTER", "UNDO"}

    creaseOffset: FloatProperty(
        name="Width",
        description="Crevice width",
        min=0.001, max=1.0,
        default=0.15,
    )

    precision: FloatProperty(
        name="Precision",
        description="Distance precision for double face detection",
        min=1e-8, max=1.0,
        default=1e-3,
    )

    subdiv: IntProperty(
        name="Subdivision Depth",
        description="Number of subdivision for inner face detection",
        min=1, max=10,
        default=1,
    )
    red_param: IntProperty(
        name="Bevel reduction",
        description="Factor to divide the resolution of all bevels",
        min=1, max=100,
        default=2,
    )
    
    def execute(self, context):
        MakeQuickLOD(self.creaseOffset, self.precision, self.subdiv, self.red_param)
        
        return {"FINISHED"}
    
    def invoke(self, context, event):
        htd = context.scene.htd
        if 'stripThick' in htd.keys():
            self.creaseOffset = float(htd['stripThick'])
        if 'bevelReduction' in htd.keys():
            self.red_param = int(htd['bevelReduction'])
        MakeQuickLOD(self.creaseOffset, self.precision, self.subdiv, self.red_param)
        return {"FINISHED"}

class MESH_OT_MakeFirstLOD(bpy.types.Operator):
    bl_idname = "mesh.make_lodone"
    bl_label = "Make LOD1 only"
    bl_options = {"REGISTER", "UNDO"}

    creaseOffset: FloatProperty(
        name="Width",
        description="Crevice width",
        min=0.001, max=1.0,
        default=0.02,
    )

    precision: FloatProperty(
        name="Precision",
        description="Distance precision for double face detection",
        min=1e-8, max=1.0,
        default=1e-3,
    )

    subdiv: IntProperty(
        name="Subdivision Depth",
        description="Number of subdivision for inner face detection",
        min=1, max=10,
        default=1,
    )

    red_param: IntProperty(
        name="Bevel reduction",
        description="Factor to divide the resolution of all bevels",
        min=1, max=100,
        default=2,
    )
    
    def execute(self, context):
        MakeLOD1Only(self.creaseOffset, self.precision, self.subdiv, self.red_param)
        
        return {"FINISHED"}

    def invoke(self, context, event):
        htd = context.scene.htd
        if 'stripThick' in htd.keys():
            self.creaseOffset = float(htd['stripThick'])
        if 'bevelReduction' in htd.keys():
            self.red_param = int(htd['bevelReduction'])
        MakeLOD1Only(self.creaseOffset, self.precision, self.subdiv, self.red_param)
        return {"FINISHED"}
    

class MESH_OT_CleanDecals(bpy.types.Operator):
    bl_idname = "mesh.clean_decals"
    bl_label = "Clean decal UV channels"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        CleanDecalUV()
        
        return {"FINISHED"}
        
class MESH_OT_HideBools(bpy.types.Operator):
    bl_idname = "mesh.hide_bools"
    bl_label = "hide/shows boolean wires"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        HideBools()
        
        return {"FINISHED"}

class MESH_OT_RemoveEmptyMat(bpy.types.Operator):
    bl_idname = "mesh.remove_emptymat"
    bl_label = "Remove Empty materials from selected object"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        removeEmptyMaterials()
        
        return {"FINISHED"}        

        
class MESH_OT_AddMainBevel(bpy.types.Operator):
    bl_idname = "mesh.add_mainbevel"
    bl_label = "Add a main bevel modifier"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        AddMainBevel()
        
        return {"FINISHED"}
                


class MESH_OT_MakeCrevice(bpy.types.Operator):
    bl_idname = "mesh.make_crevice"
    bl_label = "Inset the face and UV it to the POM1 crevice"
    bl_options = {"REGISTER", "UNDO"}

    width: FloatProperty(
        name="Width",
        description="Crevice width",
        min=0.001, max=1.0,
        default=0.01
    )


    def execute(self, context):
        MakeCrevice(self.width)
        
        return {"FINISHED"}
    
    def invoke(self, context, event):
        htd = context.scene.htd
        if 'creviceThick' in htd.keys():
            self.width = float(htd['creviceThick'])
        MakeCrevice(self.width)
        return {"FINISHED"}
    
class MESH_OT_AutoCreviceUV(bpy.types.Operator):
    bl_idname = "mesh.auto_crevice_uv"
    bl_label = "UV it to the POM1 crevice"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        LODStripUtilities.MultiAutoCreviceUV()
        
        return {"FINISHED"}
        
class MESH_OT_AddWeightBevel(bpy.types.Operator):
    bl_idname = "mesh.add_weightbevel"
    bl_label = "Add a weight bevel modifier"
    bl_options = {"REGISTER", "UNDO"}
    
    segments: IntProperty(
        name="Segments",
        description="Number of bevel segments",
        min=1, max=100,
        default=3,
    )

    def execute(self, context):
        AddWeightBevel(self.segments)
        
        return {"FINISHED"}

class MESH_OT_ReduceCylinder(bpy.types.Operator):
    bl_idname = "mesh.reduce_cylinder"
    bl_label = "Reduce cylinder loop resolution"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        ReduceCylinder()
        
        return {"FINISHED"}

class MESH_OT_IncreaseCylinder(bpy.types.Operator):
    bl_idname = "mesh.increase_cylinder"
    bl_label = "Increase cylinder loop resolution"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        IncreaseCylinder()
        
        return {"FINISHED"}
        
        

class HTD_HideAddon_Props(bpy.types.PropertyGroup):
     uvToogle: BoolProperty(
        name="Auto UV",
        description="Auto UV",
        default=True)
     pivotCursor: BoolProperty(
        name="Pivot at Cursor",
        description="Set new mesh pivot at 3D cursor",
        default=True)
     stripToogle: BoolProperty(
        name="Strip gen",
        description="Auto generate strips instead of bevels",
        default=True)
     lodNum: StringProperty(
             name="LOD num",
             description="Number of Total LOD",
             default="2")
     creviceThick: StringProperty(
        name="Crevice Thickness",
        description="Crevice Thickness",
        default="0.04")
     stripThick: StringProperty(
        name="Crevice Thickness",
        description="Crevice Thickness",
        default="0.02")
     bevelReduction: StringProperty(
        name="Bevel Reduction",
        description="Divide all bevel resolution",
        default="2")
     

        

class VIEW3D_PT_HIdeExport_panel(bpy.types.Panel):
    pass

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    bl_category = "HideExport" 
    bl_label = "HideExport" 

    def draw(self, context):
        """define the layout of the panel"""
        td = bpy.context.scene.htd

        box = self.layout.box()
        row = box.row()
        row.alignment = 'CENTER'          
        row.label(text="Export Helpers", icon = "FILE")
        row = box.row()
        row.operator("mesh.make_quicklod", text="Make LODs")
        row = box.row()
        row.operator("mesh.hide_export", text="LOD0")
        row.operator("mesh.make_lodone", text="LOD1")
        row = box.row()
        row.label(text="Options:")
        row.prop(td, 'stripToogle')
        row.prop(td, 'lodNum')
        row = box.row()
        row.prop(td, 'stripThick')
        row.prop(td, 'bevelReduction')
        row = box.row()
        row.operator("mesh.clean_decals", text="Clean decal UVs")
        row = box.row()
        row.operator("mesh.hide_bools", text="Hide/Show boolean box")
        row = box.row()
        row.operator("mesh.remove_emptymat", text="Remove empty mat")
        
        row = box.box().row(align=True)
        row.label(text="Options:")
        row.prop(td, 'uvToogle')
        row.prop(td, 'pivotCursor')
        
        box = self.layout.box()
        row = box.row()
        row.alignment = 'CENTER'          
        row.label(text="Modeling helpers", icon = "MESH_DATA")
        row = box.row()
        row.operator("mesh.add_mainbevel", text="Add Main Bevel")
        row = box.row()
        row.operator("mesh.add_weightbevel", text="Add Weight Bevel")
        row = box.row()
        # row.operator("mesh.make_crevice", text="Make Crevice")
        row.operator("mesh.make_crevice", text="Make Crevice")
        row.operator("mesh.auto_crevice_uv", text="AutoUV crevice")
        row.prop(td, 'creviceThick')
        row = box.row()
        row.operator("mesh.reduce_cylinder", text="Reduce Cylinder")
        row = box.row()
        row.operator("mesh.increase_cylinder", text="Increase Cylinder")
        
        
def register():
    bpy.utils.register_class(HTD_HideAddon_Props)
    bpy.types.Scene.htd = PointerProperty(type=HTD_HideAddon_Props)
    
    bpy.utils.register_class(VIEW3D_PT_HIdeExport_panel)
    bpy.utils.register_class(MESH_OT_HideExport)
    bpy.utils.register_class(MESH_OT_MakeQuickLOD)
    bpy.utils.register_class(MESH_OT_MakeFirstLOD)
    bpy.utils.register_class(MESH_OT_CleanDecals)
    bpy.utils.register_class(MESH_OT_HideBools)
    bpy.utils.register_class(MESH_OT_AddMainBevel)
    bpy.utils.register_class(MESH_OT_AddWeightBevel)
    bpy.utils.register_class(MESH_OT_MakeCrevice)
    bpy.utils.register_class(MESH_OT_AutoCreviceUV)
    bpy.utils.register_class(MESH_OT_RemoveEmptyMat)
    bpy.utils.register_class(MESH_OT_ReduceCylinder)
    bpy.utils.register_class(MESH_OT_IncreaseCylinder)
    


def unregister():
    bpy.utils.unregister_class(MESH_OT_IncreaseCylinder)
    bpy.utils.unregister_class(MESH_OT_ReduceCylinder)
    bpy.utils.unregister_class(MESH_OT_RemoveEmptyMat)
    bpy.utils.unregister_class(MESH_OT_AutoCreviceUV)
    bpy.utils.unregister_class(MESH_OT_MakeCrevice)
    bpy.utils.unregister_class(MESH_OT_AddWeightBevel)
    bpy.utils.unregister_class(MESH_OT_AddMainBevel)
    bpy.utils.unregister_class(MESH_OT_HideBools)
    bpy.utils.unregister_class(MESH_OT_CleanDecals)
    bpy.utils.unregister_class(MESH_OT_MakeFirstLOD)
    bpy.utils.unregister_class(MESH_OT_MakeQuickLOD)
    bpy.utils.unregister_class(MESH_OT_HideExport)
    bpy.utils.unregister_class(VIEW3D_PT_HIdeExport_panel)
    bpy.utils.register_class(HTD_HideAddon_Props)
    del bpy.types.Scene.htd
    
if __name__ == "__main__":
    register()