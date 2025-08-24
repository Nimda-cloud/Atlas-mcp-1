#!/usr/bin/env python3
"""
Створення додаткових складних 3D моделей голов
"""

import trimesh
import numpy as np
import os

def create_alien_head():
    """Створює модель голови інопланетянина"""
    # Великий витягнутий череп
    head = trimesh.creation.icosphere(subdivisions=3, radius=1.2)
    
    vertices = head.vertices.copy()
    
    # Витягуємо верх голови
    top_mask = vertices[:, 1] > 0.5
    vertices[top_mask, 1] *= 1.5
    
    # Зменшуємо підборіддя
    chin_mask = vertices[:, 1] < -0.3
    vertices[chin_mask] *= 0.7
    
    # Великі очні западини
    left_eye_socket = trimesh.creation.icosphere(radius=0.4)
    left_eye_socket.apply_translation([-0.4, 0.2, 0.8])
    
    right_eye_socket = trimesh.creation.icosphere(radius=0.4)
    right_eye_socket.apply_translation([0.4, 0.2, 0.8])
    
    head.vertices = vertices
    
    # Віднімаємо очні западини
    head = head.difference(left_eye_socket)
    head = head.difference(right_eye_socket)
    
    return head

def create_mech_warrior_head():
    """Створює голову мех-воїна"""
    # Основний корпус
    main_body = trimesh.creation.box(extents=[2.2, 2.5, 2.0])
    
    # Склоні панелі
    face_panel = trimesh.creation.box(extents=[1.8, 0.2, 1.5])
    face_panel.apply_translation([0, 1.0, 0.2])
    
    # Сенсорні антени
    antenna_left = trimesh.creation.cylinder(radius=0.08, height=1.2)
    antenna_left.apply_translation([-0.8, 1.2, 0.8])
    
    antenna_right = trimesh.creation.cylinder(radius=0.08, height=1.2)
    antenna_right.apply_translation([0.8, 1.2, 0.8])
    
    # Центральний сенсор
    center_sensor = trimesh.creation.icosphere(radius=0.25)
    center_sensor.apply_translation([0, 1.1, 0.5])
    
    # Об'єднуємо все
    mech_head = trimesh.util.concatenate([
        main_body, face_panel, antenna_left, antenna_right, center_sensor
    ])
    
    return mech_head

def create_fantasy_creature():
    """Створює голову фантастичного створіння"""
    # Основа - елліпсоїд
    head = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
    
    vertices = head.vertices.copy()
    
    # Розтягуємо у ширину
    vertices[:, 0] *= 1.3
    vertices[:, 2] *= 0.8
    
    head.vertices = vertices
    
    # Роги
    horn1 = trimesh.creation.cylinder(radius=0.1, height=1.0)
    horn1.apply_transform(trimesh.transformations.rotation_matrix(np.pi/6, [0, 0, 1]))
    horn1.apply_translation([-0.5, 0.8, 0.3])
    
    horn2 = trimesh.creation.cylinder(radius=0.1, height=1.0)
    horn2.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/6, [0, 0, 1]))
    horn2.apply_translation([0.5, 0.8, 0.3])
    
    # Об'єднуємо
    creature = trimesh.util.concatenate([head, horn1, horn2])
    
    return creature

def create_steampunk_head():
    """Створює стімпанк голову"""
    # Основа
    head = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
    
    # Механічні деталі
    gear1 = trimesh.creation.cylinder(radius=0.3, height=0.1)
    gear1.apply_translation([0.7, 0.3, 0.5])
    
    gear2 = trimesh.creation.cylinder(radius=0.2, height=0.1)
    gear2.apply_translation([-0.6, 0.1, 0.6])
    
    # Труби
    pipe1 = trimesh.creation.cylinder(radius=0.1, height=0.8)
    pipe1.apply_transform(trimesh.transformations.rotation_matrix(np.pi/3, [1, 0, 0]))
    pipe1.apply_translation([0.3, 0.6, 0.1])
    
    pipe2 = trimesh.creation.cylinder(radius=0.08, height=0.6)
    pipe2.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/4, [0, 1, 0]))
    pipe2.apply_translation([-0.4, 0.5, 0.2])
    
    # Монокль
    monocle = trimesh.creation.cylinder(radius=0.15, height=0.05)
    monocle.apply_translation([0.4, 0.2, 0.8])
    
    # Об'єднуємо
    steampunk = trimesh.util.concatenate([head, gear1, gear2, pipe1, pipe2, monocle])
    
    return steampunk

def create_futuristic_helmet():
    """Створює футуристичний шолом"""
    # Основна форма
    helmet = trimesh.creation.icosphere(subdivisions=2, radius=1.1)
    
    # Забрало
    visor = trimesh.creation.box(extents=[1.8, 0.4, 1.2])
    visor.apply_translation([0, 0.3, 0.3])
    
    # Система охолодження
    cooling_fin1 = trimesh.creation.box(extents=[0.1, 0.8, 0.6])
    cooling_fin1.apply_translation([-0.9, 0.2, 0])
    
    cooling_fin2 = trimesh.creation.box(extents=[0.1, 0.8, 0.6])
    cooling_fin2.apply_translation([0.9, 0.2, 0])
    
    cooling_fin3 = trimesh.creation.box(extents=[0.1, 0.8, 0.6])
    cooling_fin3.apply_translation([-0.7, 0.2, 0])
    
    cooling_fin4 = trimesh.creation.box(extents=[0.1, 0.8, 0.6])
    cooling_fin4.apply_translation([0.7, 0.2, 0])
    
    # Об'єднуємо
    futuristic = trimesh.util.concatenate([
        helmet, visor, cooling_fin1, cooling_fin2, cooling_fin3, cooling_fin4
    ])
    
    return futuristic

def main():
    """Створює додаткові складні моделі"""
    output_dir = "/Users/dev/Documents/GitHub/Atlas-mcp/frontend-express-standalone/models"
    
    models = {
        "alien_head.glb": create_alien_head(),
        "mech_warrior_head.glb": create_mech_warrior_head(),
        "fantasy_creature_head.glb": create_fantasy_creature(),
        "steampunk_head.glb": create_steampunk_head(),
        "futuristic_helmet.glb": create_futuristic_helmet()
    }
    
    for filename, model in models.items():
        try:
            filepath = os.path.join(output_dir, filename)
            model.export(filepath)
            print(f"Створено: {filename}")
            
            # Перевіряємо розмір файлу
            size = os.path.getsize(filepath)
            print(f"  Розмір: {size} байт")
        except Exception as e:
            print(f"Помилка при створенні {filename}: {e}")

if __name__ == "__main__":
    main()
