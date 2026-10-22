import bpy
import random
import colorsys

def apply_random_diffuse_with_full_backup(collection_name):
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        print(f"Collection '{collection_name}' introuvable.")
        return

    materials = set()
    for obj in collection.all_objects:
        if obj.type == 'MESH':
            for slot in obj.material_slots:
                if slot.material:
                    materials.add(slot.material)

    materials = list(materials)
    total_mats = len(materials)

    if total_mats == 0:
        print("Aucun matériau trouvé.")
        return

    hue_indices = list(range(total_mats))
    random.shuffle(hue_indices)

    for idx, mat in enumerate(materials):
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # 1. Sauvegarde complète de l'arbre original dans un NodeGroup dédié
        backup_group_name = f"_FULL_BACKUP_{mat.name}"
        
        if backup_group_name not in bpy.data.node_groups:
            backup_group = bpy.data.node_groups.new(name=backup_group_name, type='ShaderNodeTree')
            
            # Duplication exacte de TOUS les nœuds de l'arbre
            node_map = {}
            for node in nodes:
                copied_node = backup_group.nodes.new(type=node.bl_idname)
                node_map[node] = copied_node
                
                # Copie des propriétés spécifiques (ex: références d'images pour Image Texture)
                for prop in node.bl_rna.properties:
                    if not prop.is_readonly and prop.identifier not in {'rna_type', 'name', 'location'}:
                        try:
                            setattr(copied_node, prop.identifier, getattr(node, prop.identifier))
                        except AttributeError:
                            pass
                
                copied_node.name = node.name
                copied_node.location = node.location

                # Copie des valeurs d'entrées
                for i, inp in enumerate(node.inputs):
                    if hasattr(inp, 'default_value'):
                        try:
                            copied_node.inputs[i].default_value = inp.default_value
                        except:
                            pass

            # Duplication des connexions entre les nœuds
            for link in links:
                from_node = node_map.get(link.from_node)
                to_node = node_map.get(link.to_node)
                if from_node and to_node:
                    try:
                        from_socket = from_node.outputs[link.from_socket.name]
                        to_socket = to_node.inputs[link.to_socket.name]
                        backup_group.links.new(from_socket, to_socket)
                    except KeyError:
                        pass

            mat["backup_tree_name"] = backup_group_name

        # 2. Application du Diffuse BSDF temporaire
        nodes.clear()

        node_output = nodes.new(type='ShaderNodeOutputMaterial')
        node_output.location = (300, 0)

        node_diffuse = nodes.new(type='ShaderNodeBsdfDiffuse')
        node_diffuse.location = (0, 0)

        hue = hue_indices[idx] / total_mats
        r, g, b = colorsys.hsv_to_rgb(hue, 0.85, 0.90)
        node_diffuse.inputs['Color'].default_value = (r, g, b, 1.0)

        links.new(node_diffuse.outputs['BSDF'], node_output.inputs['Surface'])

    print(f"Modifications et sauvegarde complète appliquées pour {total_mats} matériau(x).")


def revert_materials_full(collection_name):
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        print(f"Collection '{collection_name}' introuvable.")
        return

    materials = set()
    for obj in collection.all_objects:
        if obj.type == 'MESH':
            for slot in obj.material_slots:
                if slot.material:
                    materials.add(slot.material)

    reverted_count = 0
    for mat in materials:
        backup_name = mat.get("backup_tree_name")
        if backup_name and backup_name in bpy.data.node_groups:
            backup_group = bpy.data.node_groups[backup_name]
            
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            nodes.clear()

            # Restauration exacte des nœuds depuis la sauvegarde
            node_map = {}
            for node in backup_group.nodes:
                restored_node = nodes.new(type=node.bl_idname)
                node_map[node] = restored_node
                
                # Restauration de toutes les propriétés (incluant les liens vers les fichiers images)
                for prop in node.bl_rna.properties:
                    if not prop.is_readonly and prop.identifier not in {'rna_type', 'name', 'location'}:
                        try:
                            setattr(restored_node, prop.identifier, getattr(node, prop.identifier))
                        except AttributeError:
                            pass
                
                restored_node.name = node.name
                restored_node.location = node.location

                for i, inp in enumerate(node.inputs):
                    if hasattr(inp, 'default_value'):
                        try:
                            restored_node.inputs[i].default_value = inp.default_value
                        except:
                            pass

            for link in backup_group.links:
                from_node = node_map.get(link.from_node)
                to_node = node_map.get(link.to_node)
                if from_node and to_node:
                    try:
                        from_socket = from_node.outputs[link.from_socket.name]
                        to_socket = to_node.inputs[link.to_socket.name]
                        links.new(from_socket, to_socket)
                    except KeyError:
                        pass

            # Suppression du groupe de sauvegarde temporaire
            bpy.data.node_groups.remove(backup_group)
            del mat["backup_tree_name"]
            reverted_count += 1

    print(f"Restauration exacte terminée pour {reverted_count} matériau(x).")
