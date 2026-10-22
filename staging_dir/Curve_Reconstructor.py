import bpy
import bmesh
from mathutils import Vector

def rdp_3d(points, epsilon):
    """
    Algorithme de Ramer-Douglas-Peucker en 3D.
    - points : liste de Vector()
    - epsilon : tolérance de distance maximale autorisée (en unités Blender)
    """
    if len(points) < 3:
        return points

    # Trouve le point le plus éloigné du segment formé par le premier et dernier point
    dmax = 0.0
    index = 0
    p1, p2 = points[0], points[-1]
    line_vec = (p2 - p1)
    line_len = line_vec.length

    for i in range(1, len(points) - 1):
        p = points[i]
        # Calcul de la distance orthogonale du point au segment [p1, p2]
        if line_len == 0:
            d = (p - p1).length
        else:
            # Produit vectoriel pour obtenir la distance au segment 3D
            d = line_vec.cross(p - p1).length / line_len

        if d > dmax:
            index = i
            dmax = d

    # Si la distance maximale est supérieure à epsilon, on découpe récursivement
    if dmax > epsilon:
        rec_results1 = rdp_3d(points[:index + 1], epsilon)
        rec_results2 = rdp_3d(points[index:], epsilon)
        return rec_results1[:-1] + rec_results2
    else:
        return [p1, p2]

def reconstruct_spline_from_tube(epsilon=0.02):
    obj = bpy.context.active_object
    if obj is None or obj.type != 'MESH':
        raise ValueError("Veuillez sélectionner un objet de type Maillage (Mesh).")

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    # 1. Trouver le point de départ idéal (une extrémité du tube)
    boundaries = [v for v in bm.verts if v.is_boundary]
    start_wave = set()
    radius = 0.0
    
    if boundaries:
        # Si le tube est ouvert, on récupère exactement une seule boucle de bordure
        stack = [boundaries[0]]
        while stack:
            curr = stack.pop()
            start_wave.add(curr)
            for e in curr.link_edges:
                if e.is_boundary:
                    other = e.other_vert(curr)
                    if other not in start_wave:
                        stack.append(other)
    else:
        # Si le tube est fermé (bouchons), on prend le sommet le plus éloigné du centre
        bbox_center = sum((Vector(b) for b in obj.bound_box), Vector()) / 8
        start_v = max(bm.verts, key=lambda v: (v.co - bbox_center).length)
        start_wave = {start_v}

    visited = set(start_wave)
    waves = [start_wave]
    current_wave = start_wave

    # 2. Balayage topologique (anneau par anneau) le long du tube
    while True:
        next_wave = set()
        for v in current_wave:
            for e in v.link_edges:
                other = e.other_vert(v)
                if other not in visited:
                    next_wave.add(other)
        
        if not next_wave:
            break # Fin du tube atteinte
            
        visited.update(next_wave)
        waves.append(next_wave)
        current_wave = next_wave

    # 3. Calcul des centroïdes pour chaque anneau
    center_points = []
    for wave in waves:
        centroid = sum((v.co for v in wave), Vector()) / len(wave)
        world_centroid = obj.matrix_world @ centroid
        radius = (v.co -centroid).length
        center_points.append(world_centroid)

    bm.free()

    # --- FILTRAGE SELON LA COURBURE (Ramer-Douglas-Peucker) ---
    # epsilon représente la tolérance d'écart (ex: 0.05 = 5 cm dans Blender)
    # Augmentez epsilon pour supprimer plus de points sur les lignes droites.

    center_points = rdp_3d(center_points, epsilon)
    # ---------------------------------------------------------

    if len(center_points) < 2:
        print("Erreur: Pas assez de points conservés.")
        return None

    # 4. Création de la courbe Bézier avec les points filtrés
    curve_data = bpy.data.curves.new(name="Spline_Reconstruite", type='CURVE')
    curve_data.dimensions = '3D'
    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(len(center_points) - 1)

    for i, pt in enumerate(center_points):
        bp = spline.bezier_points[i]
        bp.co = pt
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'

    curve_obj = bpy.data.objects.new("Curve_Reconstruite", curve_data)
    bpy.context.collection.objects.link(curve_obj)
    
    # Sélectionne la nouvelle courbe pour vérification
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = curve_obj
    curve_obj.select_set(True)
    bpy.context.object.data.bevel_depth = radius

