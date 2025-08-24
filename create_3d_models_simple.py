#!/usr/bin/env python3
"""
Створення простих 3D моделей голов у форматі GLB
"""

import trimesh
import numpy as np
import os

def create_human_head():
    """Створює просту модель людської голови"""
    # Створюємо сферу як основу для голови
    head = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
    
    # Трохи деформуємо для більш реалістичної форми
    vertices = head.vertices.copy()
    
    # Витягуємо підборіддя
    chin_mask = vertices[:, 1] < -0.3  # нижня частина
    vertices[chin_mask, 1] *= 0.8
    
    # Сплющуємо ззаду
    back_mask = vertices[:, 2] < -0.5
    vertices[back_mask, 2] *= 0.7
    
    head.vertices = vertices
    
    return head

def create_robot_head():
    """Створює просту модель голови робота"""
    # Створюємо куб як основу
    head = trimesh.creation.box(extents=[1.8, 2.0, 1.6])
    
    # Додаємо "очі" - маленькі сфери
    eye1 = trimesh.creation.icosphere(radius=0.2)
    eye1.apply_translation([-0.4, 0.3, 0.8])
    
    eye2 = trimesh.creation.icosphere(radius=0.2)
    eye2.apply_translation([0.4, 0.3, 0.8])
    
    # Об'єднуємо
    robot_head = trimesh.util.concatenate([head, eye1, eye2])
    
    return robot_head

def create_transformer_head():
    """Створює модель голови трансформера"""
    # Основна форма - більш кутаста
    main = trimesh.creation.box(extents=[2.0, 2.2, 1.8])
    
    # Додаємо "антени"
    antenna1 = trimesh.creation.cylinder(radius=0.05, height=0.8)
    antenna1.apply_translation([-0.6, 1.0, 0.3])
    
    antenna2 = trimesh.creation.cylinder(radius=0.05, height=0.8)
    antenna2.apply_translation([0.6, 1.0, 0.3])
    
    # Додаємо "забрало"
    visor = trimesh.creation.box(extents=[1.6, 0.3, 1.4])
    visor.apply_translation([0, 0.2, 0.1])
    
    # Об'єднуємо
    transformer = trimesh.util.concatenate([main, antenna1, antenna2, visor])
    
    return transformer

def create_android_head():
    """Створює модель голови андроїда"""
    # Основа - сфера
    head = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
    
    # Додаємо технологічні елементи
    tech_panel = trimesh.creation.box(extents=[0.8, 0.1, 0.6])
    tech_panel.apply_translation([0, 0.5, 0.3])
    
    # Світлодіодні "очі"
    led1 = trimesh.creation.cylinder(radius=0.1, height=0.1)
    led1.apply_translation([-0.3, 0.6, 0.5])
    
    led2 = trimesh.creation.cylinder(radius=0.1, height=0.1)
    led2.apply_translation([0.3, 0.6, 0.5])
    
    # Об'єднуємо
    android = trimesh.util.concatenate([head, tech_panel, led1, led2])
    
    return android

def create_cyborg_head():
    """Створює модель голови кіборга"""
    # Людська основа
    head = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
    
    # Механічна частина
    mech_part = trimesh.creation.box(extents=[0.9, 0.8, 0.4])
    mech_part.apply_translation([0.45, 0, 0.3])
    
    # Механічне око
    mech_eye = trimesh.creation.cylinder(radius=0.15, height=0.2)
    mech_eye.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    mech_eye.apply_translation([0.6, 0.2, 0.4])
    
    # Об'єднуємо
    cyborg = trimesh.util.concatenate([head, mech_part, mech_eye])
    
    return cyborg

def create_skull_head():
    """Створює модель черепа"""
    # Основа - сфера
    skull = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
    
    # Деформуємо у форму черепа
    vertices = skull.vertices.copy()
    
    # Сплющуємо боки
    side_mask = np.abs(vertices[:, 0]) > 0.7
    vertices[side_mask, 0] *= 0.8
    
    # Витягуємо лоб
    forehead_mask = (vertices[:, 1] > 0.3) & (vertices[:, 2] > 0.3)
    vertices[forehead_mask, 2] *= 1.2
    
    skull.vertices = vertices
    
    return skull

def main():
    """Основна функція для створення всіх моделей"""
    output_dir = "/Users/dev/Documents/GitHub/Atlas-mcp/frontend-express-standalone/models"
    
    models = {
        "human_head_male.glb": create_human_head(),
        "robot_head_simple.glb": create_robot_head(),
        "transformer_head.glb": create_transformer_head(),
        "android_head.glb": create_android_head(),
        "cyborg_head.glb": create_cyborg_head(),
        "skull_head.glb": create_skull_head()
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
