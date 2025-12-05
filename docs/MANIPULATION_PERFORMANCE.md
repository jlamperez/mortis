# Manipulation Performance Guide

## Model Loading Time

Cada tarea de manipulación tarda aproximadamente **10-14 segundos** en iniciarse debido a la carga del modelo SmolVLM.

### Por Qué Ocurre Esto

1. **PolicyServer mantiene el modelo** - El servidor de políticas carga el modelo en GPU
2. **RobotClient se recrea** - Cada tarea necesita un nuevo cliente (limitación de LeRobot)
3. **PolicyServer recarga el modelo** - Cuando detecta un nuevo cliente, recarga el modelo

### Tiempos Típicos

```
Primera tarea:
  - Crear PolicyServer: 2s
  - Crear RobotClient: 4s
  - Cargar modelo SmolVLM: 10s
  - Total: ~16s

Tareas subsiguientes:
  - Recrear RobotClient: 4s
  - Recargar modelo: 10s
  - Total: ~14s por tarea
```

### Por Qué No Se Puede Optimizar Más

El `control_loop()` de LeRobot solo puede ejecutarse una vez por RobotClient. Para ejecutar una nueva tarea, necesitamos:

1. **Parar el cliente anterior** - Desconecta cámaras y robot
2. **Crear nuevo cliente** - Reconecta todo
3. **PolicyServer detecta nuevo cliente** - Recarga el modelo

Este es el comportamiento esperado de la arquitectura async de LeRobot.

## Recomendaciones

### Para Desarrollo/Testing

- Usa timeouts cortos (15-20s) para iterar rápido
- Acepta los 10-14s de carga como parte del flujo
- Planifica tus pruebas para minimizar el número de tareas

### Para Producción

- Usa timeouts más largos (60-90s) para tareas complejas
- Considera agrupar múltiples acciones en una sola tarea
- El tiempo de carga es inevitable pero solo ocurre al inicio de cada tarea

### Para Demos

- Pre-carga el sistema ejecutando una tarea dummy al inicio
- Explica a la audiencia que la carga del modelo es normal
- Enfócate en la calidad de la ejecución, no en la velocidad de inicio

## Alternativas (Futuras)

Para evitar la recarga del modelo, se necesitaría:

1. **Modificar LeRobot** - Permitir que PolicyServer mantenga el modelo entre clientes
2. **Reusar RobotClient** - Permitir múltiples `control_loop()` en el mismo cliente
3. **Arquitectura diferente** - Usar un enfoque de "task queue" en lugar de recrear clientes

Estas opciones requieren cambios en LeRobot que están fuera del alcance de Mortis.

## Resumen

✅ **Comportamiento actual**: 10-14s de carga por tarea
✅ **Es esperado**: Limitación de la arquitectura de LeRobot
✅ **No es un bug**: El sistema funciona correctamente
✅ **Optimización**: Ya está optimizado dentro de las limitaciones de LeRobot

El tiempo de carga es el precio que pagamos por tener un sistema limpio y confiable que recrea el estado para cada tarea.
