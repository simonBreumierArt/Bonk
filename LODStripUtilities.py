import os
import bpy 
import math
import bmesh
import numpy as np
from mathutils import Vector
from bpy.app.handlers import persistent
from mathutils.bvhtree import BVHTree
from mathutils.geometry import intersect_point_line



def find_closest_face(pos):
    finalIndex = 0
    distMin = 10000
    i=0
    for f2 in obj.data.polygons:
        distActu = math.dist(f2.center, pos)
        if distActu < distMin:
            distMin = distActu
            finalIndex = i
        i+=1
    return finalIndex

def dot(a,b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

def select_inner_faces(obj):
    j=0
    eps = 0.1
    indexTable = []
    for f in obj.data.polygons:
        rc = obj.ray_cast(f.center+ f.normal * eps, f.normal)
        if(rc[0]):
            HitfaceIndex = find_closest_face(rc[1])
            dotProd = dot(obj.data.polygons[HitfaceIndex].normal, f.normal)
            if(dotProd > 0):
                indexTable.append(j)

        j+=1
                
    for elem in indexTable:
        obj.data.polygons[elem].select = True
            
def AddSelectedToList():
    j=0
    selectedList = []
    for p in obj.data.polygons:
        if p.select:
            for v in p.vertices:
                selectedList.append(v)
        j+=1
    return selectedList

def compareVerts(v1,v2):
    return abs(v1[0]-v2[0])<= 0.001 and abs(v1[1]-v2[1])<= 0.001 and abs(v1[2]-v2[2])<= 0.001

def compareEdges(e1, e2):
    # retBool = math.dist(e1[0], e2[0]) <= 0.001 and math.dist(e1[1], e2[1])<= 0.001
    retBool = compareVerts(e1[0], e2[0]) and compareVerts(e1[1], e2[1])
    if (retBool):
        return retBool
    # retBool2 = math.dist(e1[0], e2[1]) <= 0.001 and math.dist(e1[1], e2[0])<= 0.001
    retBool2 = compareVerts(e1[0], e2[1]) and compareVerts(e1[1], e2[0])
    # bary_1 = 0.5 * (e1[0] + e1[1])
    # bary_2 = 0.5 * (e2[0] + e2[1])
    # dir_1 = e1[1] - e1[0]
    # dir_2 = e2[1] - e2[0]
    # return dir_1.cross(dir_2) == Vector((0.0, 0.0, 0.0)) and dir_1.length == dir_2.length and math.dist(bary_1, bary_2)<= 0.001
    return retBool2 


def testFace(p, verts):
    bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(True, True, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":False, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "use_duplicated_keyframes":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
    objActu = bpy.context.selected_objects[0]
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode= 'OBJECT')
    objActu.data.polygons[p.index].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    rayOrigin = p.vertices[2]
    rc = objActu.ray_cast(verts[rayOrigin].co, p.normal)
    bpy.ops.object.delete(use_global=False)
    
    if rc[0] and math.dist(rc[1], verts[rayOrigin].co) < eps:
        return True
    else:
        return False
       
def findDoubleFaces(obj):
    fullFaceList = []
    for p in obj.data.polygons:
        for p2 in obj.data.polygons:
            if math.dist(p2.center, p.center) < 0.001 and p.index != p2.index:
                fullFaceList.append(p.index)
                fullFaceList.append(p2.index)
    for elem in fullFaceList:
        obj.data.polygons[elem].select = True

def selectActivate(objName):
    bpy.context.scene.objects[objName].select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.scene.objects[objName]

def testfaceIsDouble(obj, p, eps, subdiv=1):
    isDouble = False

    if obj.ray_cast(p.center + eps * p.normal, p.normal)[0]:
        objName = obj.name
        p.select = True
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((0, 0, 0), (0, 0, 0), (0, 0, 0)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "use_duplicated_keyframes":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
        objDup = bpy.context.selected_objects[0]
        objDup.name = "DuplicateMesh"
        objDup = bpy.context.scene.objects["DuplicateMesh"]

        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode = 'OBJECT')
        objActu = bpy.context.selected_objects[1]
        objActu.name = "SingleFace"
        bpy.ops.object.select_all(action='DESELECT')
        selectActivate("SingleFace")

        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.subdivide(number_cuts=subdiv)
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        isDouble = True
        for f in objActu.data.polygons:                       
            rc1 = objDup.ray_cast(f.center - eps * f.normal, f.normal, distance=0.1)
            rc2 = objDup.ray_cast(f.center + eps * f.normal, -f.normal, distance=0.1)
            if (rc1[0] == False or math.dist(rc1[1], f.center) > eps) and (rc2[0] == False or math.dist(rc2[1], f.center) > eps):
                isDouble = False
                break

        objDup.select_set(True)
        objActu.select_set(True)
        bpy.context.view_layer.objects.active = bpy.context.scene.objects["DuplicateMesh"]
        bpy.ops.object.delete(use_global=False, confirm=False)

        bpy.context.scene.objects[objName].select_set(True)
        bpy.context.view_layer.objects.active = bpy.context.scene.objects[objName]
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode = 'OBJECT')

        
    return isDouble

def selectInnerDoubleFaces(obj, subdiv, eps=1e-3): 
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT')
    me = obj.data
    bm = bmesh.from_edit_mesh(me) 
    doubleVert = bmesh.ops.find_doubles(bm, verts=bm.verts, dist=eps)["targetmap"]
    indexList = []
    for v in doubleVert.keys():
        for p in v.link_faces:
            if not(p.index in indexList):
                indexList.append(p.index)
        for p in doubleVert[v].link_faces:
            if not(p.index in indexList):
                indexList.append(p.index)
    bpy.ops.object.mode_set(mode = 'OBJECT')

    faceIndex = []
    for pind in indexList:
        if testfaceIsDouble(obj, obj.data.polygons[pind], eps, subdiv):
            faceIndex.append(pind)

    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bpy.ops.object.mode_set(mode = 'OBJECT')
    for pind in faceIndex:
        obj.data.polygons[pind].select = True  
    return faceIndex             

def testfaceIsFullyCovered_optimized(bvh, bm, p, eps=1e-3):
    """
    Détermine si la face 'p' est entièrement recouverte ou coïncidente.
    Gère : faces parfaitement superposées (doublons), micro-quads et n-gons concaves.
    """
    face_normal = p.normal
    face_center = p.calc_center_median()

    # --- ÉTAPE 1 : Test rapide de coïncidence parfaite (Anti Z-Fighting) ---
    # On cherche s'il existe une face dont le centre est EXACTEMENT au même endroit
    # (rayon très serré = eps * 0.1)
    exact_overlaps = bvh.find_nearest_range(face_center, eps * 0.1)
    for location, normal, face_index, distance in exact_overlaps:
        if face_index != p.index:
            hit_face = bm.faces[face_index]
            # Si les normales sont alignées sur le même plan
            if abs(hit_face.normal.dot(face_normal)) > 0.999:
                return True # Court-circuit : coïncidence parfaite trouvée !

    # --- ÉTAPE 2 : Triangulation locale pour l'échantillonnage de surface ---
    sample_points = []
    if len(p.verts) == 3:
        sample_points.append(face_center)
    # else:
    #     # Duplication temporaire en mémoire pour extraire les vrais centres
    #     bm_temp = bmesh.new()
    #     verts_temp = [bm_temp.verts.new(v.co) for v in p.verts]
    #     face_temp = bm_temp.faces.new(verts_temp)
    #     tri_result = bmesh.ops.triangulate(bm_temp, faces=[face_temp])

    #     # On parcourt directement les faces triangulées retournées par l'opération
    #     for f_tri in tri_result["faces"]:
    #         sample_points.append(f_tri.calc_center_median())
            
    #     bm_temp.free()

    # Ajouter les sommets légèrement rétractés
    for v in p.verts:
        reference_inside_point = min(sample_points, key=lambda pt: (pt - v.co).length_squared)
        vec_in = reference_inside_point - v.co
        border_point = v.co + vec_in * 0.1
        sample_points.append(border_point)

    # --- ÉTAPE 3 : Lancer de rayons pour les recouvrements partiels / accolés ---
    for point in sample_points:
        covered = False
        
        # On augmente l'offset à (eps * 2) pour s'extirper proprement de la surface 
        # et éviter que le rayon ne s'auto-intersecte avec la face d'origine
        offsets = [eps * 2, -eps * 2]
        
        for offset in offsets:
            ray_origin = point + face_normal * offset
            ray_direction = -face_normal if offset > 0 else face_normal
            
            location, normal, face_index, distance = bvh.ray_cast(ray_origin, ray_direction)
            
            # La distance maximale autorisée pour toucher la face couvrante est élargie à (eps * 4)
            if location is not None and face_index != p.index:# and distance < (eps * 4):
                hit_face = bm.faces[face_index]
                if abs(hit_face.normal.dot(face_normal)) > 0.99:
                    covered = True
                break 
                    
        if not covered:
            return False

    return True


def selectInnerDoubleFaces_optimized(obj, eps=1e-3): 
    # 1. S'assurer qu'on est en mode ÉDITION pour manipuler le BMesh de l'Edit Mesh
    if obj.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
        
    # Désélectionner tout via les outils classiques au départ
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT')
    
    me = obj.data
    bm = bmesh.from_edit_mesh(me) 
    bm.faces.ensure_lookup_table()
    
    # 2. Création du BVH à partir du BMesh actif
    bvh = BVHTree.FromBMesh(bm)
    
    # Trouver les sommets doublons
    doubleVert = bmesh.ops.find_doubles(bm, verts=bm.verts, dist=eps)["targetmap"]
    
    # Collecter les indices uniques des faces liées aux sommets doublons
    indexList = set()  # Utiliser un set() évite les vérifications manuelles "if not in" (O(1) vs O(N))
    for v in doubleVert.keys():
        for p in v.link_faces:
            indexList.add(p.index)
        for p in doubleVert[v].link_faces:
            indexList.add(p.index)
            
    faceIndex = []
    
    # 3. Boucle de détection (Tout reste en mémoire dans le BMesh valide)
    for pind in indexList:
        # Récupérer l'instance BMFace valide depuis la table
        p = bm.faces[pind]
        
        # Appel de la fonction optimisée
        if testfaceIsFullyCovered_optimized(bvh, bm, p, eps):
            faceIndex.append(pind)
            
    # 4. Appliquer la sélection directement dans le BMesh en mode Édition
    for pind in faceIndex:
        bm.faces[pind].select = True
        
    # 5. Forcer Blender à rafraîchir l'affichage du mode Édition pour afficher la sélection
    bmesh.update_edit_mesh(me)
    
    # (Optionnel) Si vous avez absolument besoin de repasser en mode OBJET à la fin :
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    return faceIndex

def normalizeVector(v):
    factor = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    if factor == 0:
        return v
    else:
        return v / factor


# def vertexIsInEdge(v, e):
#     vectAB = e.verts[1].co - e.verts[0].co
#     vectVB = v.co - e.verts[0].co
#     return math.dist(normalizeVector(vectAB), normalizeVector(vectVB)) <1e-6 and math.dist(vectVB, (0,0,0)) < math.dist(vectAB, (0,0,0)) 

import mathutils

def vertexIsInEdge_opti(v, e, tolerance=1e-5):
    if v in e.verts:
        return True
    pt = v.co
    p1 = e.verts[0].co
    p2 = e.verts[1].co
    if p1.x < p2.x:
        if pt.x < p1.x - tolerance or pt.x > p2.x + tolerance: return False
    else:
        if pt.x < p2.x - tolerance or pt.x > p1.x + tolerance: return False

    if p1.y < p2.y:
        if pt.y < p1.y - tolerance or pt.y > p2.y + tolerance: return False
    else:
        if pt.y < p2.y - tolerance or pt.y > p1.y + tolerance: return False

    if p1.z < p2.z:
        if pt.z < p1.z - tolerance or pt.z > p2.z + tolerance: return False
    else:
        if pt.z < p2.z - tolerance or pt.z > p1.z + tolerance: return False

    nearest_pt, factor = mathutils.geometry.intersect_point_line(pt, p1, p2)

    if -tolerance <= factor <= 1.0 + tolerance:
        if (pt - nearest_pt).length_squared <= tolerance * tolerance:
            return True

    return False

def vertexIsInEdge(v, e, tolerance=1e-5):
    if v in e.verts:
        return True
    pt = v.co
    p1 = e.verts[0].co
    p2 = e.verts[1].co

    nearest_pt, factor = intersect_point_line(pt, p1, p2)
    if 0.0 <= factor <= 1.0:
        if (pt - nearest_pt).length <= tolerance:
            return True

    return False

def findVertexInEdges(bm, e):
    vertsInEdge = []
    for v in bm.verts:
        if vertexIsInEdge_opti(v, e) and not (math.dist(e.verts[0].co, v.co) < 1e-6 or math.dist(e.verts[1].co, v.co) < 1e-6):
            vertsInEdge.append(v.co)
    return vertsInEdge

def findVertexInEdges_opti(bm, e, tolerance=1e-5):
    # S'assurer que les tables de référence BMesh sont à jour
    bm.verts.ensure_lookup_table()
    
    # CORRECTION : L'unpacking direct ou la conversion en liste est obligatoire pour extraire v1 et v2
    v1, v2 = e.verts
    p1, p2 = v1.co, v2.co

    tolerance_sq = tolerance * tolerance
    
    # Si vous voulez uniquement les sommets FLOTTANTS (sans les extrémités), initialisez à []
    # Si vous voulez TOUS les sommets de l'arête, laissez [v1, v2]
    vertices_on_edge = []
    
    min_x, max_x = min(p1.x, p2.x) - tolerance, max(p1.x, p2.x) + tolerance
    min_y, max_y = min(p1.y, p2.y) - tolerance, max(p1.y, p2.y) + tolerance
    min_z, max_z = min(p1.z, p2.z) - tolerance, max(p1.z, p2.z) + tolerance

    for v in bm.verts:
        if v == v1 or v == v2:
            continue  
        pt = v.co
        if not (min_x <= pt.x <= max_x and 
                min_y <= pt.y <= max_y and 
                min_z <= pt.z <= max_z):
            continue
            
        nearest_pt, factor = mathutils.geometry.intersect_point_line(pt, p1, p2)
        if -tolerance <= factor <= 1.0 + tolerance:
            if (pt - nearest_pt).length_squared <= tolerance_sq:
                vertices_on_edge.append(v)
                
    return vertices_on_edge

def detectSingleFace(obj):
    bpy.ops.object.mode_set(mode='EDIT')
    me = obj.data
    bm = bmesh.from_edit_mesh(me)
    for e in bm.edges:
        if e.is_boundary and e.select:
            vertsInEdge = findVertexInEdges_opti(bm, e)
            if len(vertsInEdge) > 0:
                ret = bmesh.ops.bisect_edges(bm, edges=[e], cuts =len(vertsInEdge))

                for vactu in vertsInEdge:
                    closerDist = 1e8
                    for i in range(0, len(vertsInEdge)):
                        distActu = math.dist(ret["geom_split"][i].co, vactu)
                        if  distActu < closerDist:
                            closerDist = distActu
                            iClose = i
                    ret["geom_split"][iClose].co = vactu  
                bpy.ops.mesh.remove_doubles()
    
     
    bpy.ops.object.mode_set(mode='OBJECT')

import bpy
import bmesh
import mathutils

def detectSingleFace_opti(obj, tolerance=1e-5):
    bpy.ops.object.mode_set(mode='EDIT')
    me = obj.data
    bm = bmesh.from_edit_mesh(me)
    
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    
    # 1. PHASE 1 : ANALYSE (Lecture seule - Strictement aucun risque de crash)
    edges_to_bisect = []
    edges_cuts_count = []
    # Dictionnaire pour associer l'index de la future arête créée à la coordonnée cible
    # Clé : (coordonnée approximative p1 de l'arête, index du cut), Valeur : coordonnée du vertex flottant
    target_positions = {} 
    
    tolerance_sq = tolerance * tolerance

    for e in bm.edges:
        if not (e.is_boundary and e.select):
            continue
            
        v1, v2 = e.verts
        p1, p2 = v1.co.copy(), v2.co.copy()
        
        # Boîte englobante
        min_x, max_x = min(p1.x, p2.x) - tolerance, max(p1.x, p2.x) + tolerance
        min_y, max_y = min(p1.y, p2.y) - tolerance, max(p1.y, p2.y) + tolerance
        min_z, max_z = min(p1.z, p2.z) - tolerance, max(p1.z, p2.z) + tolerance
        
        verts_on_edge = []
        for v in bm.verts:
            if v == v1 or v == v2:
                continue
            pt = v.co
            if not (min_x <= pt.x <= max_x and min_y <= pt.y <= max_y and min_z <= pt.z <= max_z):
                continue
                
            nearest_pt, factor = mathutils.geometry.intersect_point_line(pt, p1, p2)
            if -tolerance <= factor <= 1.0 + tolerance:
                if (pt - nearest_pt).length_squared <= tolerance_sq:
                    verts_on_edge.append((v.co.copy(), factor))
                    
        if verts_on_edge:
            # Trier les sommets cibles du début vers la fin de l'arête
            verts_on_edge.sort(key=lambda item: item[1])
            
            edges_to_bisect.append(e)
            edges_cuts_count.append(len(verts_on_edge))
            
            # Stocker les positions cibles ordonnées pour cette arête spécifique
            # On utilise le tuple de la coordonnée de départ pour identifier l'arête de manière immuable
            for idx, (target_co, factor) in enumerate(verts_on_edge):
                target_positions[(tuple(p1), idx)] = target_co

    # Si aucune arête ne nécessite de découpe, on s'arrête là
    if not edges_to_bisect:
        return

    # 2. PHASE 2 : DÉCOUPE GLOBALE (Une seule opération C++ pour tout le maillage)
    # On passe TOUTES les arêtes d'un coup. Blender gère les allocations mémoire proprement en interne.
    for e, cuts in zip(edges_to_bisect, edges_cuts_count):
        p1_orig = e.verts[0].co.copy()
        
        ret = bmesh.ops.bisect_edges(bm, edges=[e], cuts=cuts)
        
        # Récupérer les nouveaux sommets générés pour cette découpe
        new_verts = [item for item in ret["geom_split"] if isinstance(item, bmesh.types.BMVert)]
        # Les trier par rapport au point de départ de l'arête d'origine
        new_verts.sort(key=lambda nv: (nv.co - p1_orig).length_squared)
        
        # Aligner précisément les positions
        for idx, nv in enumerate(new_verts):
            key = (tuple(p1_orig), idx)
            if key in target_positions:
                nv.co = target_positions[key]

    # 3. PHASE 3 : FUSION ET NETTOYAGE
    bm.verts.ensure_lookup_table()
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=tolerance)
    
    bmesh.update_edit_mesh(me)

    
def getNumConnectFace(faceActu): 
    numConectFace = 0
    for e in faceActu.edges:
        if not(e.is_boundary):
            numConectFace +=1
    return numConectFace


def cleanStripIntersection(obj, eps):
    hasChanged = True
    while hasChanged:
        hasChanged = False
        bpy.ops.object.mode_set(mode='EDIT')
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        for faceActu in bm.faces:
            numConectFace = getNumConnectFace(faceActu)
            
            if numConectFace > 2:
                SplitEdgeList = bmesh.ops.split_edges(bm, edges=[faceActu.edges[0]]) 

                edgeCoords = []
                bm.edges.ensure_lookup_table()
                
                for v in faceActu.edges[0].verts:
                    for e in v.link_edges:
                        if not faceActu in e.link_faces:
                            edgeCoords.append(e.index)
                
                V1 = bm.edges[edgeCoords[0]].verts[0].co
                V2 = bm.edges[edgeCoords[0]].verts[1].co
                V3 = bm.edges[edgeCoords[1]].verts[0].co
                V4 = bm.edges[edgeCoords[1]].verts[1].co

                def dmnop(m, n, o, p):
                    return (m[0] - n[0]) * (o[0] - p[0]) + (m[1] - n[1]) * (o[1] - p[1]) + (m[2] - n[2]) * (o[2] - p[2])

                mua = dmnop(V1, V3, V4, V3) * dmnop(V4, V3, V2, V1) - dmnop(V1, V3, V2, V1) * dmnop(V4, V3, V4, V3)
                muadet = dmnop(V2, V1, V2, V1) * dmnop(V4, V3, V4, V3) - dmnop(V4, V3, V2, V1) * dmnop(V4, V3, V2, V1)
                if muadet < eps:
                    P = (faceActu.edges[0].verts[0].co + faceActu.edges[0].verts[1].co) / 2
                else:
                    P = V1 + (mua / muadet) * (V2 - V1)

                distV1V2 = max(math.dist(V2 - V1, (0,0,0)), 1e-6)
                distV4V3 = max(math.dist(V4 - V3, (0,0,0)), 1e-6)
                vectAB = (V2 - V1) / distV1V2
                vectCD = (V4 - V3) /  distV4V3
                if not(vectAB == vectCD or vectAB == -vectCD):
                    for e in SplitEdgeList["edges"]:
                        if not (e.index == faceActu.edges[0].index):
                            if math.dist(e.verts[0].co, P) < math.dist(e.verts[1].co, P):
                                e.verts[0].co = P
                            else:
                                e.verts[1].co = P
                
                bmesh.ops.pointmerge(bm, verts=faceActu.edges[0].verts, merge_co = P)
                hasChanged = True

        bpy.ops.object.mode_set(mode='OBJECT')

def mergeVerts():
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
    bpy.ops.mesh.remove_doubles()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
    bpy.ops.object.mode_set(mode = 'OBJECT')

def mergeVert_silent(obj):
    if obj and obj.type == 'MESH':
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        bm.to_mesh(obj.data)
        bm.free() # Libérer la mémoire
        obj.data.update()

def selectEdgeList(edgeList, obj):
    bpy.ops.object.mode_set(mode='EDIT')
    nb_vgroup = len(obj.vertex_groups)
    obj.vertex_groups.active_index = nb_vgroup-1
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.mode_set(mode = 'OBJECT')
    idList = []
    for e in edgeList:
        for e2 in obj.data.edges:
            if e2.select:
                vActu = (obj.data.vertices[e2.vertices[0]].co, obj.data.vertices[e2.vertices[1]].co)
                if compareEdges(vActu, e):
                    idList.append(e2.index)
                    break
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode = 'OBJECT')
    for id in idList:
        obj.data.edges[id].select = True

def selectEdgeList_optimized(edgeList, obj, tolerance=4):
    # 1. Sélectionner le vertex group initial (comme dans ton code d'origine)
    bpy.ops.object.mode_set(mode='EDIT')
    if obj.vertex_groups:
        obj.vertex_groups.active_index = len(obj.vertex_groups) - 1
        bpy.ops.object.vertex_group_select()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Fonction interne pour créer une clé unique et robuste (gère l'ordre des sommets et les arrondis)
    def get_edge_key(v1, v2):
        p1 = (round(v1.x, tolerance), round(v1.y, tolerance), round(v1.z, tolerance))
        p2 = (round(v2.x, tolerance), round(v2.y, tolerance), round(v2.z, tolerance))
        # On trie les points pour que (A,B) et (B,A) donnent la même clé
        return tuple(sorted([p1, p2]))

    # 2. Créer un dictionnaire de correspondance (Hash Map) des arêtes sélectionnées
    # On évite la boucle imbriquée : O(M) pour construire, puis O(1) par recherche
    edge_dict = {}
    vertices = obj.data.vertices
    
    for e2 in obj.data.edges:
        if e2.select:
            v0_co = vertices[e2.vertices[0]].co
            v1_co = vertices[e2.vertices[1]].co
            key = get_edge_key(v0_co, v1_co)
            edge_dict[key] = e2.index

    # 3. Rechercher les arêtes de ta liste dans le dictionnaire en un temps record
    idList = []
    for e in edgeList:
        # e est supposé être un tuple (v_start, v_end)
        key = get_edge_key(e[0], e[1])
        if key in edge_dict:
            idList.append(edge_dict[key])

    # 4. Réinitialiser la sélection
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 5. Appliquer la nouvelle sélection finale
    for idx in idList:
        obj.data.edges[idx].select = True  

def selectFaceList(faceList, obj):
    for p in faceList:
        obj.data.polygons[p].select = True

def reduce_bevel(obj, red_param=2):
    for mod in obj.modifiers:
        if mod.type == "BEVEL" and not "MainBevel" in mod.name:
            mod.segments = math.ceil(mod.segments/red_param)

def tri_area( co1, co2, co3 ):
    return (co2 - co1).cross( co3 - co1 ).length / 2.0

def quick_td_resize(obj, target=10.24, res=2048):
    me = obj.data
    bm = bmesh.from_edit_mesh(me) 

    # Ensure faces access
    bm.faces.ensure_lookup_table()

    # Triangulate it so that we can calculate tri areas
    triangle_loops = bm.calc_loop_triangles()

    # Get the uv map
    uv_loop = bm.loops.layers.uv['UVMap']

    # Initialize face entries
    areas = {face: (0.0, 0.0) for face in bm.faces} 

    # enumerate the loops
    for loop in triangle_loops[:1]:
        # Get the face
        face = loop[0].face
        # Get current areas
        face_area, uv_area = areas[face]
        # Add tri surface area
        face_area += tri_area( *(l.vert.co for l in loop) )
        # Add corresponding uv surface area
        uv_area += tri_area( *(Vector( (*l[uv_loop].uv, 0) ) for l in loop) )
        # Set the result in the dictionary
        areas[face] = (face_area, uv_area)

    face_area, uv_area = areas[face]
    tdActu = math.sqrt(uv_area / face_area)*res/100
    fact = target / tdActu
    # bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    for face in obj.data.polygons:
            for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                obj.data.uv_layers.active.data[loop_idx].uv *= fact     
    bpy.ops.object.mode_set(mode='EDIT')    

def create_face_inset(obj):
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bpy.ops.object.mode_set(mode = 'OBJECT')
    if isAnyFaceSelected(obj):
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.context.selected_objects[1].name = "FaceDuplicates"
        bpy.context.selected_objects[0].name = "Strips"
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects["FaceDuplicates"].select_set(True)
        bpy.context.view_layer.objects.active = bpy.context.scene.objects["FaceDuplicates"]
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.inset(thickness=0.03, depth=0)
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

def create_strips(obj_dup, edgeList, CreaseOffset, eps=1e-3):
    selectEdgeList_optimized(edgeList, obj_dup)
    # for e in edgeList:
    #     for e2 in obj_dup.data.edges:
    #         vActu = (obj_dup.data.vertices[e2.vertices[0]].co, obj_dup.data.vertices[e2.vertices[1]].co)
    #         if compareEdges(vActu, e):
    #             e2.select = True
    #             break
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.bevel(offset=CreaseOffset, offset_pct=0, affect='EDGES')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.mesh.delete(type='FACE')
    bpy.ops.object.mode_set(mode = 'OBJECT')
    if "FaceDuplicates" in bpy.context.scene.objects:
        bpy.context.scene.objects["FaceDuplicates"].select_set(True)
        bpy.ops.object.join()

    cleanStripIntersection(obj_dup, eps)

@persistent 
def HideExport_fbx(addTriang, red_param=1):
    htd = bpy.context.scene.htd
    if 'uvToogle' in htd.keys():
        doUVs = htd['uvToogle']
    else:
        doUVs = True
    
    if 'pivotCursor' in htd.keys():
        doPivotAtCursor = htd['pivotCursor']
    else:
        doPivotAtCursor = True
    
    
    mat_exclude_list = ["POM_Decals_01", "POM_Decals_02", "Signaletique_01", "Signaletique_02"]
    basedir = os.path.dirname(bpy.data.filepath)

    col_name = bpy.context.collection.name
    
    if not basedir:
        raise Exception("Blend file is not saved")

    view_layer = bpy.context.view_layer

    obj_active = view_layer.objects.active

    i=0
    for obj in bpy.data.collections[col_name].all_objects: 
        if obj.type == 'MESH' or obj.type == 'CURVE':
            obj.select_set(True)
        if obj.type == 'MESH':
            view_layer.objects.active = obj
            if len(obj.data.uv_layers) > 0:
                obj.data.uv_layers[0].name = "UVMap"
                for uvActu in reversed(obj.data.uv_layers[1:]):
                    obj.data.uv_layers.remove(uvActu)
        
        
    # Merge, apply modifiers and transforms
    bpy.ops.object.duplicate()
    if red_param > 1:
        for obj_actu in bpy.context.selected_objects:
            reduce_bevel(obj_actu, red_param)
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.make_single_user(object=True, obdata=True, material=False, animation=False, obdata_animation=False)
    bpy.ops.object.join()
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.context.selected_objects[0].name = col_name

    ############################
    newMesh = bpy.context.selected_objects[0]
    mat_list = [m.name for m in bpy.data.materials]
    object_mats = newMesh.material_slots
    i = 0
    td_context = bpy.context.scene.td
    td_context['texture_size'] = 2
    treated = []

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')


    for matActu in object_mats:
        matActuName = matActu.name
        newMesh.active_material_index = i
        if not(matActu in treated):
            if '_id' in matActu.name:
                if not(matActuName[:-3] in mat_list): 
                    newMesh.material_slots[matActuName].material = newMesh.material_slots[matActuName].material.copy() 
                    newMesh.active_material.name = matActuName[:-3]
                else:
                    newMesh.material_slots[matActuName].material = bpy.data.materials[matActuName[:-3]]
                treated.append(matActuName)
                treated.append(matActuName[:-3])
            else:
                bpy.ops.object.editmode_toggle()
                # bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.material_slot_select()
                # if(doUVs):
                #     bpy.ops.uv.cube_project(cube_size=2) 
                #     #bpy.context.scene.texToolsSettings.size_dropdown = '2048'
                #     bpy.ops.object.preset_set(td_value="10.24")
                #     # quick_td_resize(bpy.context.selected_objects[0], target=10.24, res=2048)
                #     bpy.ops.object.texel_density_set()
                
                    #bpy.context.scene.texToolsSettings.size_dropdown = '2048'
                #Cube unwrap to get 10.24 px/cm in 2K since I can't change default size dropdown from 512...      
                bpy.ops.object.editmode_toggle() 
                treated.append(matActuName)           
        i+=1
    if(doUVs):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.uv.cube_project(cube_size=2) 
        #bpy.context.scene.texToolsSettings.size_dropdown = '2048'
        bpy.ops.object.preset_set(td_value="10.24")
        # quick_td_resize(bpy.context.selected_objects[0], target=10.24, res=2048)
        bpy.ops.object.texel_density_set()
        bpy.ops.object.mode_set(mode='OBJECT')

    ############################
    if(addTriang):
        bpy.ops.object.modifier_add(type='TRIANGULATE')
        bpy.context.object.modifiers["Triangulate"].keep_custom_normals = True
    
    if not ('Export' in bpy.data.collections.keys()):
        exportCol = bpy.data.collections.new("Export")
        bpy.context.scene.collection.children.link(exportCol)
    else:
        exportCol = bpy.data.collections['Export']
    
    exportCol.objects.link(bpy.context.selected_objects[0])
    wasInChildren = False
    for colactu in bpy.data.collections[col_name].children_recursive:
        if col_name in colactu.objects.keys():
            colactu.objects.unlink(bpy.context.selected_objects[0])
            wasInChildren = True
    if not(wasInChildren):
        bpy.context.collection.objects.unlink(bpy.context.selected_objects[0])
    
    if doPivotAtCursor:
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.context.object.location[0] = 0
        bpy.context.object.location[1] = 0
        bpy.context.object.location[2] = 0

def MultiAutoCreviceUV(useID=True):
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode = 'OBJECT')
    toUV = []
    for objActu in bpy.context.selected_objects:
        toUV.append(objActu.name)
    bpy.ops.object.select_all(action='DESELECT')
    for elem in toUV:
        bpy.context.scene.objects[elem].select_set(True)
        bpy.context.view_layer.objects.active = bpy.context.scene.objects[elem]
        AutoCreviceUV(useID)
        bpy.ops.object.modifier_add(type='DISPLACE')
        bpy.context.object.modifiers["Displace"].strength = 0.01
        bpy.ops.object.shade_auto_smooth()
        bpy.ops.object.select_all(action='DESELECT')

    for elem in toUV:
        bpy.context.scene.objects[elem].select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.join()

def AutoCreviceUV(useID=True):
    obj = bpy.context.selected_objects[0]

    if(len(obj.data.polygons) > 0):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.context.scene.tool_settings.use_uv_select_sync = False
        bpy.ops.uv.cube_project(cube_size=1)
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.uv_squares_by_shape()
        bpy.ops.object.editmode_toggle()
        

        x_list = []
        y_list = []
        for face in obj.data.polygons:
            for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                uv_coords = obj.data.uv_layers.active.data[loop_idx].uv
                y_list.append(uv_coords[1])
                x_list.append(uv_coords[0])  

        

        x_list = np.unique(x_list)        
        y_list = np.unique(y_list)
        rot_id = 0
        fin_list = y_list
        stop_bool = False
        if len(y_list) > len(x_list):
            rot_id = 1
            fin_list = x_list
        elif len(y_list) == len(x_list) and not(len(y_list) == 2):
            stop_bool = True

        maxX = 0
        minX = 1e6
        if not stop_bool:
            for face in obj.data.polygons:
                for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                    uv_coords = obj.data.uv_layers.active.data[loop_idx].uv
                    new_y = 0.0
                    if uv_coords[1-rot_id] in  fin_list[0:-1:2]:
                        new_y = 0.996
                    else:
                        new_y = 0.979
                    obj.data.uv_layers.active.data[loop_idx].uv = Vector((uv_coords[rot_id], new_y))
                    maxX = max(maxX, uv_coords[rot_id])
                    minX = min(minX, uv_coords[rot_id])
            divFactor = max(1.0, abs(maxX - minX))
            
            for face in obj.data.polygons:
                for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                    uv_coords = obj.data.uv_layers.active.data[loop_idx].uv
                    obj.data.uv_layers.active.data[loop_idx].uv = Vector((uv_coords[0] / divFactor, uv_coords[1]))

        if useID:
            matName = 'POM_Decals_01_id'
        else: 
            matName = 'POM_Decals_01'
        
        if not(matName in bpy.data.materials.keys()):
            bpy.data.materials.new(matName)

        if (len(obj.material_slots) == 0):
            bpy.ops.object.material_slot_add()
        bpy.context.selected_objects[0].material_slots[0].material = bpy.data.materials[matName]
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.context.object.active_material_index = 0
        bpy.ops.object.material_slot_assign()
        bpy.ops.object.mode_set(mode='OBJECT')

    # else:
    #     bpy.ops.object.delete(use_global=False)


def isAnyFaceSelected(obj):
    existSelected = False
    for p in obj.data.polygons:
        if p.select:
            existSelected = True
            break
    return existSelected

#######################################################
def createLOD1(col_name, eps=1e-3, subdiv=2, CreaseOffset=0.15, red_param=2):
    # if len(bpy.context.selected_objects) > 0:
    #     col_name = bpy.context.selected_objects[0].users_collection[0].name
    col_name = bpy.context.collection.name
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.collection.objects[0].select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.collection.objects[0]

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    for obj in bpy.data.collections[col_name].all_objects: 
        if "MainBevel" in obj.modifiers:
            obj.modifiers["MainBevel"].show_viewport = False
        if "MainBevel.001" in obj.modifiers:
            obj.modifiers["MainBevel.001"].show_viewport = False
        if "MainBevel.002" in obj.modifiers:
            obj.modifiers["MainBevel.002"].show_viewport = False

    bpy.context.collection.name = col_name + "_LOD1"
    HideExport_fbx(False, red_param=red_param)
    bpy.ops.object.modifier_add(type='TRIANGULATE')
    bpy.context.object.modifiers["Triangulate"].keep_custom_normals = True
    bpy.ops.object.modifier_apply(modifier="Triangulate", report=True)
    obj_initial = bpy.data.objects[col_name+"_LOD1"]
    obj_initial.select_set(True)
    bpy.context.view_layer.objects.active = obj_initial
    bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((0, 0, 0), (0, 0, 0), (0, 0, 0)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "use_duplicated_keyframes":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
    obj_dup = bpy.context.selected_objects[0]
    obj_dup.name = "Strips"

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode= 'OBJECT')
    



    #doubleFaceIndex = selectInnerDoubleFaces(obj_dup, subdiv)
    doubleFaceIndex = selectInnerDoubleFaces_optimized(obj_dup, eps)
    ###########################
    obj_dup = bpy.context.scene.objects["Strips"]
    edgeList = []
    for p in obj_dup.data.polygons:
        if p.select:
            for e in p.edge_keys:
                edgeList.append((obj_dup.data.vertices[e[0]].co.copy(), obj_dup.data.vertices[e[1]].co.copy()))
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.vertex_group_add()
    nb_vgroup = len(obj_dup.vertex_groups)
    obj_dup.vertex_groups.active_index = nb_vgroup-1
    bpy.ops.object.vertex_group_assign()

    bpy.ops.mesh.delete(type='FACE')
    bpy.context.view_layer.objects.active = bpy.context.scene.objects["Strips"]
    mergeVerts()
    #mergeVert_silent(bpy.context.active_object)
    selectEdgeList_optimized(edgeList, obj_dup)        
    detectSingleFace_opti(obj_dup)
    # mergeVerts()
    # selectEdgeList(edgeList, obj_dup) 
    
    ###Create face insets
    create_face_inset(obj_dup)
    bpy.context.scene.objects["Strips"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.scene.objects["Strips"]
    obj_dup = bpy.context.scene.objects["Strips"]

    #############################
    ########### Create Strips
    create_strips(obj_dup, edgeList, CreaseOffset, eps)

    ######## Auto UV
    if len(obj_dup.data.polygons) > 0:
        MultiAutoCreviceUV(useID=False)
        obj_strip = bpy.context.selected_objects[0]
        obj_strip.name = "Strips"
        bpy.context.scene.objects["Strips"].select_set(False)  
    else:
        bpy.data.objects.remove(bpy.context.scene.objects["Strips"])
    
    bpy.context.scene.objects[col_name+"_LOD1"].select_set(True)    
    bpy.context.view_layer.objects.active = bpy.context.scene.objects[col_name+"_LOD1"]
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bpy.ops.object.mode_set(mode = 'OBJECT')
    selectFaceList(doubleFaceIndex, bpy.context.scene.objects[col_name+"_LOD1"])
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.delete(type='FACE')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles()
    bpy.ops.object.mode_set(mode = 'OBJECT')

    if "Strips" in bpy.context.scene.objects:
        bpy.context.scene.objects["Strips"].select_set(True) 
    bpy.ops.object.join()

    bpy.ops.object.modifier_add_node_group(asset_library_type='ESSENTIALS', asset_library_identifier="", relative_asset_identifier="geometry_nodes\\smooth_by_angle.blend\\NodeTree\\Smooth by Angle")
    bpy.ops.object.modifier_add(type='TRIANGULATE')
    bpy.context.object.modifiers["Triangulate"].keep_custom_normals = True
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
        
    ####Cleanup initial collection
    bpy.context.collection.name = bpy.context.collection.name[:-5]
    for obj in bpy.data.collections[col_name].all_objects: 
        if "MainBevel" in obj.modifiers:
            obj.modifiers["MainBevel"].show_viewport = True
        if "MainBevel.001" in obj.modifiers:
            obj.modifiers["MainBevel.001"].show_viewport = True
        if "MainBevel.002" in obj.modifiers:
            obj.modifiers["MainBevel.002"].show_viewport = True
        

