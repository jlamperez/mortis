# Solución al Problema de Cámaras Bloqueadas

## Problema
Cuando `ENABLE_MANIPULATION=true`, LeRobot bloquea las cámaras durante la inferencia y Gradio no puede acceder a la webcam.

## Soluciones Implementadas

### ✅ Solución 1: Liberación Automática de Cámaras (RECOMENDADA)

He implementado un sistema que libera automáticamente las cámaras cuando LeRobot no las está usando.

**Configuración en `.env`:**
```bash
LEROBOT_RELEASE_CAMERAS_WHEN_IDLE=true
```

**Cómo funciona:**
1. Cuando una tarea de manipulación termina → LeRobot desconecta las cámaras
2. Gradio puede acceder a la webcam libremente
3. Cuando empieza una nueva tarea → LeRobot reconecta las cámaras automáticamente

**Ventajas:**
- ✅ Permite usar Gradio webcam y LeRobot simultáneamente
- ✅ Completamente automático
- ✅ Funciona con las 3 cámaras

**Desventajas:**
- ⚠️ Pequeño delay (~1-2 segundos) al iniciar tareas por la reconexión de cámaras
- ⚠️ No sirve si necesitas streaming continuo de cámaras

### 🔧 Solución 2: Usar una Cámara Diferente para Gradio

Si tienes 3 cámaras y LeRobot usa 2 (índices 0 y 8), puedes configurar tu navegador para usar la tercera.

**Paso 1: Identificar cámaras disponibles**
```bash
make list-cameras
```

Este comando te mostrará todas las cámaras disponibles y cuáles están en uso.

**Paso 2: Configurar el navegador**
1. Cuando Gradio pida permiso de cámara, haz clic en el icono de cámara en la barra de direcciones
2. Selecciona "Configuración de cámara"
3. Elige una cámara diferente (no la 0 ni la 8)
4. Recarga la página de Gradio

### 🔄 Solución 3: Reiniciar la Aplicación

Si las cámaras siguen bloqueadas:

```bash
# Detener completamente (Ctrl+C)
# Luego reiniciar
make run
```

## Configuración Recomendada

Tu archivo `.env` debería tener:

```bash
# Habilitar manipulación
ENABLE_MANIPULATION=true

# Liberar cámaras cuando están inactivas (RECOMENDADO)
LEROBOT_RELEASE_CAMERAS_WHEN_IDLE=true

# Configuración de cámaras LeRobot (por defecto)
# Cámara 1: RealSense (serial: 030522070314) - índices /dev/video0-6
# Cámara 2: OpenCV (índice: 8) - /dev/video8
# Cámara 3: Disponible para Gradio - /dev/video2 o similar
```

## Comandos Útiles

```bash
# Listar todas las cámaras disponibles
make list-cameras

# Ver qué procesos están usando las cámaras
sudo lsof /dev/video* 2>/dev/null

# Probar una cámara específica
ffmpeg -f v4l2 -i /dev/video2 -frames:v 1 test.jpg
```

## Flujo de Trabajo Recomendado

1. **Configurar** `LEROBOT_RELEASE_CAMERAS_WHEN_IDLE=true` en `.env`
2. **Iniciar** la aplicación con `make run`
3. **Usar** Gradio webcam normalmente
4. **Ejecutar** tareas de manipulación cuando sea necesario
5. Las cámaras se liberan automáticamente después de cada tarea

## Notas Técnicas

### Implementación
- Nuevo parámetro `release_cameras_when_idle` en `LeRobotAsyncClient`
- Métodos `_release_cameras()` y `_reconnect_cameras()` para gestión automática
- Las cámaras se desconectan después de cada tarea completada/fallida/interrumpida
- Las cámaras se reconectan automáticamente antes de cada nueva tarea

### Rendimiento
- Delay de reconexión: ~1-2 segundos
- No afecta la calidad de la inferencia
- Ideal para uso interactivo (no para streaming continuo)

### Compatibilidad
- ✅ OpenCV cameras
- ✅ RealSense cameras
- ✅ Cualquier cámara compatible con LeRobot

## Troubleshooting

### Las cámaras siguen bloqueadas
```bash
# Verificar procesos usando cámaras
sudo lsof /dev/video*

# Matar proceso si es necesario
kill -9 <PID>

# Reiniciar aplicación
make run
```

### Gradio no detecta ninguna cámara
```bash
# Listar cámaras disponibles
make list-cameras

# Verificar permisos
ls -la /dev/video*

# Probar cámara manualmente
ffmpeg -f v4l2 -i /dev/video2 -frames:v 1 test.jpg
```

### Delay muy largo al iniciar tareas
Si el delay de reconexión es muy largo (>5 segundos):
- Verifica que las cámaras estén correctamente conectadas
- Revisa los logs para errores de conexión
- Considera desactivar `LEROBOT_RELEASE_CAMERAS_WHEN_IDLE=false` si necesitas respuesta inmediata

## Documentación Adicional

- [Camera Troubleshooting Guide (English)](CAMERA_TROUBLESHOOTING.md)
- [LeRobot Documentation](https://github.com/huggingface/lerobot)
