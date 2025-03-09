#!/usr/bin/env python3
"""
Script para ejecutar la migración de IDs enteros a UUIDs.
"""

import os
import sys

# Añadir el directorio de la aplicación al path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from migrations.uuid_migration import run_migration

if __name__ == "__main__":
    print("Iniciando proceso de migración...")
    run_migration()
    print("Proceso de migración finalizado.") 