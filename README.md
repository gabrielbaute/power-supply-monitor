# Power Supply Monitor (PSM)
Version: 0.3.0

Servicio ligero en Python diseñado para monitorear el estado de la fuente de alimentación eléctrica (AC) en servidores alojados en laptops (Ubuntu/Linux) y enviar alertas en tiempo real mediante **ntfy**.

Permite diferenciar entre fallos de red/conectividad y cortes reales de energía eléctrica aprovechando la interfaz del sistema de archivos sysfs (`/sys/class/power_supply`).

---

## 🚀 Despliegue con Docker Compose

La forma recomendada de desplegar la aplicación es mediante Docker Compose, mapeando la interfaz del kernel en modo lectura (`ro`).

### 1. Clonar e iniciar el servicio

```bash
# Iniciar el servicio en segundo plano
docker compose up -d --build
```

### 2. Verificar logs

```bash
docker compose logs -f
```

---

## ⚙️ Variables de Entorno

El servicio se configura mediante variables de entorno que pueden definirse en un archivo `.env` o directamente en el archivo `docker-compose.yml`:

| Variable | Descripción | Valor por Defecto | Ejemplo / Requerido |
| --- | --- | --- | --- |
| `NTFY_URL` | URL base de la instancia de ntfy. | *Ninguno* | `https://ntfy.sh` *(Requerido)* |
| `NTFY_TOPIC` | Nombre del canal o tema donde se emitirán las alertas. | *Ninguno* | `mis_servidores_alerts` *(Requerido)* |
| `AC_SUPPLY_NAME` | Nombre del dispositivo AC en `/sys/class/power_supply/`. | `AC0` | `AC`, `AC0`, `ADP1` |
| `SUPPLY_PATH` | Ruta base del sistema de archivos `sysfs` para energía. | `/sys/class/power_supply` | `/sys/class/power_supply` |
| `CHECK_INTERVAL` | Intervalo en segundos entre cada comprobación de estado. | `5` | `10` |
| `LOG_LEVEL` | Nivel de registro de logs (`DEBUG`, `INFO`, `WARNING`, `ERROR`). | `INFO` | `DEBUG` |

---

## 🛠️ Estructura del docker-compose.yml

```yaml
services:
  power-monitor:
    build: .
    container_name: power_supply_monitor
    restart: always
    environment:
      - NTFY_URL=https://ntfy.sh
      - NTFY_TOPIC=tu_topic_privado
      - AC_SUPPLY_NAME=AC0
      - CHECK_INTERVAL=5
      - LOG_LEVEL=INFO
    volumes:
      - /sys/class/power_supply:/sys/class/power_supply:ro
      - ./logs:/app/logs
```
