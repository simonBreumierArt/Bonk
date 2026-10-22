import bpy
import bmesh
from math import floor

def clamp_uv():
    obj = bpy.context.active_object
    if not obj or obj.type != 'MESH':
        print("Veuillez sélectionner un objet de type Maillage.")
        return

    is_edit_mode = (obj.mode == 'EDIT')
    if not is_edit_mode:
        bpy.ops.object.mode_set(mode='EDIT')

    bm = bmesh.from_edit_mesh(obj.data)
    uv_layer = bm.loops.layers.uv.verify()

    # 1. Construit un graphe d'adjacence basé STRICTEMENT sur la continuité UV
    # Deux faces sont connectées seulement si elles partagent une arête ET les mêmes coordonnées UV
    face_neighbors = {f: set() for f in bm.faces}
    edge_uv_map = {}

    for face in bm.faces:
        for loop in face.loops:
            edge = loop.edge
            # Clé unique pour le point UV : (coordonnée X, coordonnée Y)
            uv_coords = (round(loop[uv_layer].uv.x, 5), round(loop[uv_layer].uv.y, 5))
            
            # On stocke les loops qui partagent les mêmes sommets 3D et la même position UV
            key = (edge, loop.vert)
            
            if key not in edge_uv_map:
                edge_uv_map[key] = []
            edge_uv_map[key].append(face)

    # Lier les faces qui se touchent VRAIMENT dans l'espace UV
    for face in bm.faces:
        for loop in face.loops:
            edge = loop.edge
            for linked_face in edge.link_faces:
                if linked_face != face:
                    # Vérifie si le bord est continu en UV
                    l1 = next(l for l in face.loops if l.edge == edge)
                    l2 = next(l for l in linked_face.loops if l.edge == edge)
                    
                    uv1_a, uv1_b = l1[uv_layer].uv, l1.link_loop_next[uv_layer].uv
                    uv2_a, uv2_b = l2[uv_layer].uv, l2.link_loop_next[uv_layer].uv
                    
                    # Si les coordonnées UV coïncident au bord
                    if (abs(uv1_a.x - uv2_a.x) < 0.0001 and abs(uv1_a.y - uv2_a.y) < 0.0001) or \
                       (abs(uv1_a.x - uv2_b.x) < 0.0001 and abs(uv1_a.y - uv2_b.y) < 0.0001):
                        face_neighbors[face].add(linked_face)

    # 2. Grouper les îlots selon la continuité UV réelle
    unvisited = set(bm.faces)
    islands = []

    while unvisited:
        seed = unvisited.pop()
        island = set([seed])
        stack = [seed]
        
        while stack:
            curr = stack.pop()
            for neighbor in face_neighbors[curr]:
                if neighbor in unvisited:
                    unvisited.remove(neighbor)
                    island.add(neighbor)
                    stack.append(neighbor)
        
        islands.append(island)

    # 3. Appliquer le décalage X sur chaque îlot individuellement
    modified_count = 0
    for island in islands:
        u_coords = [loop[uv_layer].uv.x for face in island for loop in face.loops]
        if not u_coords:
            continue
            
        min_u = min(u_coords)
        max_u = max(u_coords)
        center_u = (min_u + max_u) / 2.0
        
        # Nombre de décalages entiers
        shift_x = -floor(center_u)

        if shift_x != 0:
            modified_count += 1
            for face in island:
                for loop in face.loops:
                    loop[uv_layer].uv.x += shift_x

    bmesh.update_edit_mesh(obj.data)

    if not is_edit_mode:
        bpy.ops.object.mode_set(mode='OBJECT')
