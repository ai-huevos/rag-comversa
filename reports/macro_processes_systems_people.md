# MACRO PROCESOS, SISTEMAS Y PERSONAS INVOLUCRADAS
## Análisis Consolidado de 44 Entrevistas (Los Tajibos, Comversa, Bolivian Foods)

**Fecha de Generación:** 2025-11-12
**Fuente de Datos:** 1,743 entidades consolidadas (PostgreSQL + Neo4j)
**Total de Entidades:** 170 Procesos | 183 Sistemas | 137 Flujos de Datos | 17 Empleados

---

## ÍNDICE
1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Procesos por Empresa](#procesos-por-empresa)
3. [Sistemas Tecnológicos](#sistemas-tecnológicos)
4. [Flujos de Datos Críticos](#flujos-de-datos-críticos)
5. [Matriz de Roles y Responsabilidades](#matriz-de-roles-y-responsabilidades)
6. [Mapeo Proceso-Sistema-Persona](#mapeo-proceso-sistema-persona)

---

## 1. RESUMEN EJECUTIVO

### Estadísticas Generales
- **Total de Macro Procesos Identificados:** 170
- **Procesos de Alta Frecuencia (Diarios):** ~60%
- **Sistemas en Uso:** 183 sistemas distintos
- **Flujos de Datos Críticos:** 50+ flujos identificados
- **Personal Entrevistado:** 17 personas clave

### Distribución por Empresa
- **LOS TAJIBOS:** 1 empleado entrevistado (Hotelería - Marriott)
- **COMVERSA:** 7 empleados entrevistados (Corporativo/Holding)
- **BOLIVIAN FOODS:** 9 empleados entrevistados (Restaurantes/Alimentos)

---

## 2. PROCESOS POR EMPRESA

### 2.1. PROCESOS CRÍTICOS (Frecuencia Diaria, Alto Impacto)

#### 🏨 LOS TAJIBOS - Hotel & Eventos
**Operaciones Hoteleras Core:**
1. **Check In y Check Out de Huéspedes** (Diario)
   - Sistema: Opera PMS
   - Personal: Front Desk, Recepción

2. **Atención de huéspedes y resolución de incidencias** (Diario)
   - Sistemas: Opera, Jira Service Management, Control Panel
   - Personal: Gerencia de Pisos, Front Office, Mantenimiento

3. **Asignación de habitaciones e inventario** (Diario)
   - Sistema: Opera PMS
   - Personal: Recepción, Housekeeping

4. **Inspección de habitaciones** (Diario)
   - Sistemas: Opera, Control Panel (llaves móviles)
   - Personal: Housekeeping Supervisors

5. **Control de lencería en habitaciones** (Diario)
   - Sistemas: Excel, Opera
   - Personal: Housekeeping

**Mantenimiento & Ingeniería:**
6. **Gestión integral de mantenimiento** (Diario)
   - Sistemas: MaintainX, Excel, WhatsApp
   - Personal: Jefe de Mantenimiento, Técnicos

7. **Coordinación de Mantenimiento** (Diario)
   - Sistemas: WhatsApp, MaintainX, Excel
   - Personal: Mantenimiento, Operaciones

8. **Actualización de planillas de mantenimiento** (Diario)
   - Sistemas: Excel, MaintainX
   - Personal: Supervisores de Mantenimiento

9. **Chequeo de estado de sistemas** (Diario)
   - Sistemas: BMS (Building Management System), Enersis
   - Personal: Ingeniería

10. **Mantenimiento y mejora continua de edificios y espacios verdes** (Diario)
    - Personal: Mantenimiento, Jardinería

**Eventos & Banquetes:**
11. **Supervisión de eventos** (Diario, 3 menciones)
    - Sistemas: Opera, Excel, Teams
    - Personal: Coordinador de Eventos, Gerente de A&B

12. **Planificación y ejecución de eventos** (Diario)
    - Sistemas: Opera, Excel, Microsoft Office
    - Personal: Eventos, Banquetes, Cocina

**Alimentos & Bebidas:**
13. **Control de costos de alimentos** (Diario)
    - Sistemas: SAP, Excel, Micros/Simphony
    - Personal: Jefe de Cocina, Controller de A&B

14. **Creación y estandarización de recetas** (As needed)
    - Sistemas: SAP, Excel
    - Personal: Chef Ejecutivo

15. **Capacitación del personal de cocina** (Ongoing, 2 menciones)
    - Sistemas: BK University (Burger King), Capacitación RRHH
    - Personal: Chef, RRHH

**Compras & Almacén:**
16. **Gestión Integral de Almacenes** (Diario)
    - Sistemas: SAP, Excel
    - Personal: Jefe de Almacén

17. **Despacho y Distribución de Insumos** (Diario)
    - Sistemas: SAP, WhatsApp
    - Personal: Almacén, Solicitantes

18. **Almacenamiento de Insumos** (Diario)
    - Sistema: SAP
    - Personal: Almacén

**TI & Comunicaciones:**
19. **Gestión de tickets** (Diario, 2 menciones)
    - Sistemas: Jira Service Management, Power Automate
    - Personal: Soporte TI

20. **Gestión y supervisión de infraestructura tecnológica** (Diario)
    - Sistemas: PRTG, Meraki, FortiClient VPN, Fileserver
    - Personal: Gerente de TI

21. **Monitoreo de telecomunicaciones** (Diario)
    - Sistemas: Grandstream Access Points, MIKROTIK, Meraki Cloud
    - Personal: Técnicos de Redes

22. **Monitoreo y análisis de sistemas y red de comunicaciones** (Diario)
    - Sistemas: Sistema de monitoreo, Jira Service Management
    - Personal: TI

---

#### 🍔 BOLIVIAN FOODS - Restaurantes & Producción de Alimentos
**Operaciones de Restaurantes:**
1. **Gestión de Ventas B2B** (Diario)
   - Sistemas: CRM (en implementación), WhatsApp, Excel
   - Personal: Gerente Comercial

2. **Monitoreo del Desempeño de Ventas** (Semanal)
   - Sistemas: SAP, Excel, Simphony/Micros
   - Personal: Gerente de Operaciones

3. **Proceso de Atención y Acompañamiento al Cliente** (Diario)
   - Sistemas: POS (Simphony/Micros), Opera (si aplica)
   - Personal: Gerentes de Tienda, Meseros

4. **Manejo de Quejas de Clientes** (Diario)
   - Sistemas: WhatsApp, Correo, Sistema de tickets
   - Personal: Gerente de Tienda, Servicio al Cliente

**Compras & Logística:**
5. **Gestión de Compras** (Diario)
   - Sistemas: SAP, Excel, WhatsApp
   - Personal: Jefe de Compras

6. **Gestión de Documentación y Cumplimiento Normativo** (Diario)
   - Sistemas: SAP, Archivos físicos y digitales
   - Personal: Compras, Legal

7. **Coordinación con proveedores** (As needed, 2 menciones)
   - Sistemas: WhatsApp, Correo, Teléfono
   - Personal: Compras, Gerencia

**Finanzas & Contabilidad:**
8. **Elaboración de Estados Financieros** (Mensual)
   - Sistemas: SAP, Excel
   - Personal: Contador General (Alejandra Flores, Micaela Gonzales)

9. **Cálculo del Costo de Ventas** (Mensual)
   - Sistemas: SAP, Excel
   - Personal: Controller, Contabilidad

10. **Conciliación Bancaria** (Mensual)
    - Sistemas: SAP, Bancos online
    - Personal: Tesorería

11. **Conciliación de Pagos y Ventas** (Diario)
    - Sistemas: SAP, Simphony, Deliverect
    - Personal: Contabilidad

12. **Gestión de tesorería y contabilidad** (Diario)
    - Sistemas: SAP, Bancos
    - Personal: Luis La Fuente (Tesorero)

13. **Administración y Emisión de Medios de Pago** (Diario)
    - Sistemas: SAP, Bancos
    - Personal: Tesorería

14. **Administración de Cuentas Bancarias e Inversiones** (Mensual)
    - Sistemas: SAP, Portales bancarios
    - Personal: Tesorería, Finanzas

**Impuestos & Cumplimiento:**
15. **Determinación del Impuesto a las Transacciones** (Mensual)
    - Sistemas: SAP, Sistema tributario
    - Personal: Contabilidad

16. **Asesoramiento para Fiscalizaciones** (Según requerimiento)
    - Sistemas: SAP, Archivos físicos
    - Personal: Contador, Legal

17. **Coordinación y seguimiento de auditorías externas** (Anual)
    - Sistemas: SAP, Excel, Documentación
    - Personal: Contador, Auditoría Interna

**Producción & Calidad:**
18. **Control de dotación de materiales** (Diario)
    - Sistemas: SAP, Centro de Producción
    - Personal: Producción

19. **Análisis de cartas de menú** (Mensual)
    - Sistemas: Excel, SAP, Recetas base
    - Personal: Chef, Gerencia Comercial

**Planificación & Estrategia:**
20. **Preparación y actualización de presentaciones para Directorio** (Mensual)
    - Empleado: Fabian Doria Medina
    - Sistemas: PowerPoint, Excel, SAP

21. **Coordinación y elaboración del presupuesto de gestión** (Anual)
    - Sistemas: SAP, Excel
    - Personal: Controller, Finanzas

22. **Plan Estratégico Anual** (Anual)
    - Personal: Alta Gerencia, Directorio
    - Sistemas: PowerPoint, Excel

---

#### 🏢 COMVERSA - Corporativo & Holding
**Análisis & Reportería:**
1. **Análisis estratégico de información** (Semanal, 2 menciones)
   - Empleados: Camila Roca, Gabriela Loza
   - Sistemas: Excel, Power BI, DATAWAREHOUSE

2. **Gestión de informes y datos** (Diario)
   - Sistemas: Excel, Hadoop DB, MySQL, MariaDB
   - Personal: Analistas de Datos

3. **Elaboración de informes mensuales al directorio** (Mensual)
   - Sistemas: Excel, PowerPoint, SAP
   - Personal: CFO, Gerentes

4. **Elaboración de informes y comunicación con la dirección** (Mensual)
   - Sistemas: Microsoft Office, SAP
   - Personal: Gerencia

5. **Generación de informes operativos** (Daily|Weekly)
   - Sistemas: SAP, Excel, BI tools
   - Personal: Operaciones

6. **Preparación de KPIs** (Mensual)
   - Sistemas: Excel, Power BI
   - Personal: Analistas

7. **Análisis de KPIs de negocios actuales** (Mensual)
   - Sistemas: Excel, SAP, BI
   - Personal: Gerencia, Analistas

**TI & Desarrollo:**
8. **Desarrollo de software** (Diario)
   - Sistemas: Visual Studio, Node.js, Angular, Flutter, GitHub, Docker
   - Personal: Nicolas Monje (Dev Team)

9. **Evaluación de servicios tecnológicos** (Semanal)
   - Sistemas: Mesh, Monday.com
   - Personal: Gerente de TI

10. **Gestión de recursos humanos en TI** (Mensual)
    - Personal: Gerente de TI, RRHH

**Proyectos & Desarrollo de Negocios:**
11. **Gestión de Proyectos de Desarrollo** (As needed)
    - Sistemas: Monday.com, Excel
    - Personal: Project Managers

12. **Evaluación de nuevos emprendimientos** (As needed)
    - Sistemas: Excel, PowerPoint
    - Personal: Samuel Doria Medina Auza, Directorio

13. **Evaluación de proyectos financieros** (As needed)
    - Sistemas: Excel, SAP
    - Personal: Finanzas, Directorio

14. **Desarrollo de nuevos locales** (As needed)
    - Sistemas: AutoCAD, Excel, Proyecto
    - Personal: Construcción, Desarrollo

**Construcción & Obras:**
15. **Gestión de Proyectos de Construcción** (Diario)
    - Sistemas: AutoCAD, Excel, WhatsApp
    - Personal: Jefe de Obras

**Comunicación Corporativa:**
16. **Gestión de Comunicación Corporativa** (Diario)
    - Sistemas: Microsoft Office, Canva
    - Personal: Comunicaciones

**Seguridad & Cumplimiento:**
17. **Cumplimiento de normativas de seguridad y salud ocupacional** (Diario)
    - Sistemas: Normativa (digital y libros)
    - Personal: Seguridad Industrial

18. **Gestión de documentación y registros ambientales y de seguridad** (Mensual)
    - Sistemas: Archivos físicos y digitales
    - Personal: Seguridad, Medio Ambiente

19. **Implementación y monitoreo de programas de prevención de riesgos laborales** (Semanal)
    - Personal: Seguridad Industrial

**Auditoría Interna:**
20. **Planificación Anual de Auditoría** (Anual)
    - Personal: Juan Jose Castellon (Auditor Interno)
    - Sistemas: Excel, SAP

21. **Ejecución de Auditoría** (Según requerimiento)
    - Personal: Auditoría Interna
    - Sistemas: SAP, Excel, Documentación

22. **Emisión de Informes de Auditoría** (Según necesidad)
    - Personal: Auditoría Interna
    - Sistemas: Microsoft Office

---

### 2.2. PROCESOS ESTRATÉGICOS (Frecuencia Mensual/Anual)

#### Financieros:
- **Planificación Financiera** (Mensual)
- **Elaboración de proyecciones y estimaciones de flujo de efectivo** (Mensual)
- **Elaboración y presentación de estados financieros a entes reguladores** (Trimestral)
- **Elaboración de Estados de Cuentas** (Mensual)
- **Cierre mensual de ingresos** (Mensual)
- **Ejecución de rendiciones de fondos** (Mensual)

#### Gestión de Personal:
- **Evaluación de desempeño y métricas** (Mensual)
- **Actualización de datos del personal** (Semanal)
- **Gestión de horarios del equipo de housekeeping** (Semanal)

#### Mantenimiento:
- **Elaboración del plan de mantenimiento** (Mensual)
- **Planificación y programación de mantenimiento** (Mensual)
- **Mantenimiento Preventivo** (Semanal)

---

## 3. SISTEMAS TECNOLÓGICOS

### 3.1. SISTEMAS CORE (Alta Frecuencia de Uso)

#### 🔴 CRÍTICOS - ERP & PMS
1. **SAP** - Sistema ERP principal
   - **Empresas:** Bolivian Foods, Comversa, Los Tajibos
   - **Módulos:** Finanzas, Compras, Inventarios, RRHH, Contabilidad
   - **Usuarios:** ~30+ usuarios mencionados
   - **Procesos:** 50+ procesos conectados
   - **Estado:** En proceso de migración desde CMNet

2. **Opera PMS** (Property Management System)
   - **Empresa:** Los Tajibos (Marriott)
   - **Funciones:** Reservas, Check-in/out, Housekeeping, Eventos
   - **Integraciones:** SAP, Marriott platforms, Satcom, Control Panel
   - **Usuarios:** Front Desk, Housekeeping, Eventos, Contabilidad

3. **Simphony / Micros** - Sistema POS Restaurantes
   - **Empresa:** Bolivian Foods, Los Tajibos (F&B)
   - **Función:** Punto de venta, gestión de mesas, ordenes
   - **Integraciones:** SAP, Satcom, Deliverect
   - **Usuarios:** Restaurantes, Cocina, Contabilidad

#### 🟠 IMPORTANTES - Gestión Operativa
4. **Microsoft Excel**
   - **Todas las empresas**
   - **Usos:** Reportería, análisis, planificación, control
   - **Procesos:** 100+ menciones en flujos de datos
   - **Estado:** Herramienta más utilizada cross-empresa

5. **MaintainX** - Gestión de Mantenimiento
   - **Empresa:** Los Tajibos
   - **Función:** CMMS (Computerized Maintenance Management System)
   - **Integraciones:** Excel, Opera PMS, SAP
   - **Usuarios:** Mantenimiento, Ingeniería

6. **Jira Service Management**
   - **Empresas:** Los Tajibos, Comversa
   - **Función:** Gestión de tickets IT, seguimiento de incidencias
   - **Integraciones:** Power Automate, Sistema de monitoreo
   - **Usuarios:** Soporte TI

7. **Satcom** - Sistema de Facturación
   - **Empresa:** Los Tajibos
   - **Función:** Facturación electrónica
   - **Integraciones:** Opera, Simphony, SAP
   - **Usuarios:** Contabilidad, Front Office

#### 🟡 SOPORTE - Comunicación & Colaboración
8. **Microsoft Teams**
   - **Todas las empresas**
   - **Función:** Comunicación interna, reuniones
   - **Usuarios:** Toda la organización

9. **WhatsApp / WhatsApp Business**
   - **Todas las empresas**
   - **Función:** Comunicación rápida, coordinación operativa
   - **Usos:** Mantenimiento, Compras, Ventas, Coordinación
   - **Flujos de datos:** 10+ flujos identificados

10. **Microsoft Outlook**
    - **Todas las empresas**
    - **Función:** Email corporativo
    - **Usuarios:** Toda la organización

#### 🟢 ESPECÍFICOS POR ÁREA

**Finanzas & Contabilidad:**
- **CMNet** (en migración a SAP) - Sistema contable legacy
- **Portales bancarios** - Gestión de cuentas y pagos
- **Sistema tributario** - Cumplimiento impositivo

**Mantenimiento & Ingeniería:**
- **BMS (Building Management System)** - Control de edificio inteligente
- **Enersis** - Gestión energética
- **PRTG** - Monitoreo de red

**Redes & TI:**
- **Meraki** / **Meraki Cloud** - Gestión de red WiFi
- **FortiClient VPN** - Acceso remoto seguro
- **Fortinet** - Firewall y seguridad
- **MIKROTIK** - Routers
- **Grandstream Access Points** - Puntos de acceso WiFi

**Ventas & Distribución:**
- **Deliverect** - Integración delivery apps
- **Booking** - Reservas hoteleras OTA
- **Expedia** - Reservas hoteleras OTA
- **CRM** (en implementación) - Gestión de clientes

**Desarrollo & Tecnología:**
- **Visual Studio / Visual Code** - IDEs desarrollo
- **Node.js** - Runtime JavaScript
- **Angular** - Framework frontend
- **Flutter** - Framework mobile
- **Docker** - Contenedores
- **GitHub** - Control de versiones
- **SQL Server / MySQL / MariaDB / Hadoop DB** - Bases de datos

**Marriott Specific (Los Tajibos):**
- **Marriott Global Source (MGS)** - Portal de compras Marriott
- **Empowered GXP** - Sistema de gestión Marriott
- **Control Panel** - Gestión de llaves móviles
- **Móvil Key** - Llaves móviles huéspedes
- **GuestVoice / Medallia** - Encuestas satisfacción huéspedes
- **BK University** - Capacitación (Burger King)

**Herramientas de Productividad:**
- **Microsoft Office Suite** (Word, PowerPoint, Excel)
- **Microsoft 365 Admin Center**
- **Microsoft Planner**
- **OneDrive / Google Drive** - Almacenamiento cloud
- **Notion** - Gestión de proyectos (mencionado)
- **Monday.com** - Gestión de proyectos
- **Canva** - Diseño gráfico

**Herramientas de Análisis:**
- **Power BI** (inferido, no explícito)
- **DATAWAREHOUSE** (en planificación/proyecto)

**IA & Automatización:**
- **Chat GPT** - Asistente IA
- **Claude** - Asistente IA (Anthropic)
- **Copilot** - Asistente IA Microsoft
- **Power Automate** - Automatización de flujos

**Otros:**
- **AutoCAD** - Diseño técnico
- **IZI Kioscos** - Autoservicio
- **Menu APP** - Menús digitales
- **Nonious** - Sistema de gestión (no especificado uso)
- **Salar** - Sistema mencionado (no especificado uso)

---

### 3.2. SISTEMAS POR EMPRESA

#### 🏨 LOS TAJIBOS (Marriott)
**Core Systems:**
- Opera PMS
- SAP
- Simphony/Micros
- Satcom
- MaintainX

**Marriott Ecosystem:**
- Marriott Global Source (MGS)
- Empowered GXP
- Control Panel (llaves móviles)
- Móvil Key
- GuestVoice/Medallia

**Infraestructura:**
- BMS (Building Management System)
- Enersis (Gestión energética)
- PRTG (Monitoreo red)
- Meraki/Meraki Cloud (WiFi)
- Fortinet (Seguridad)
- MIKROTIK (Routing)
- Grandstream (Access Points)

**IT & Soporte:**
- Jira Service Management
- FortiClient VPN
- Active Directory
- Azure AD
- Microsoft 365

**General:**
- Excel (omnipresente)
- Teams
- WhatsApp
- Outlook

---

#### 🍔 BOLIVIAN FOODS
**Core Systems:**
- SAP (migración desde CMNet)
- Simphony/Micros POS
- Deliverect (delivery integration)

**Operaciones:**
- CRM (en implementación)
- Centro de Producción (sistema)
- Recetas base (sistema)

**Logística:**
- MAERSK (transporte)
- DHL (courier)
- DELPA (proveedor)

**Finanzas:**
- CMNet (legacy, en migración)
- Portales bancarios
- Sistema tributario

**Capacitación:**
- BK University (Burger King)
- Capacitación RRHH

**General:**
- Excel (reporting masivo)
- SAP
- WhatsApp
- Teams
- Office 365

---

#### 🏢 COMVERSA (Holding)
**Desarrollo:**
- Visual Studio/Visual Code
- Node.js
- Angular
- Flutter
- Docker
- GitHub

**Bases de Datos:**
- SQL Server
- MySQL
- MariaDB
- Hadoop DB
- DATAWAREHOUSE (proyecto)

**Gestión de Proyectos:**
- Monday.com
- Mesh
- Notion

**Análisis & BI:**
- Excel
- Power BI (inferido)
- Flujo de información de los ejecutivos (sistema custom)

**Construcción & Obras:**
- AutoCAD
- IFC (Building Information Modeling)

**General:**
- SAP (corporate)
- Office 365
- Teams
- WhatsApp
- IA tools (Chat GPT, Claude, Copilot)

---

## 4. FLUJOS DE DATOS CRÍTICOS

### 4.1. FLUJOS DE INTEGRACIÓN CORE

#### Ecosistema SAP (Centro Neurálgico)
```
[Opera PMS] ──→ [SAP] ──→ [Excel] ──→ [Reportes Directorio]
      │
      ├──→ [Simphony/Micros] ──→ [SAP]
      │
      └──→ [Satcom Facturación] ──→ [SAP]

[SAP] ──→ [MaintainX] (planificado)
[SAP] ──→ [Proveedores externos]
[SAP] ──→ [Recetas base]
```

**Criticidad:** 🔴 Máxima
**Frecuencia:** Diaria
**Manual/Automático:** Mayormente manual (conciliaciones en Excel)
**Pain Points:**
- Conciliación manual Opera → SAP (1-2 horas diarias)
- Diferencias entre sistemas requieren validación
- Falta de integración en tiempo real

---

#### Ecosistema de Mantenimiento
```
[WhatsApp solicitud] ──→ [Excel registro] ──→ [MaintainX] ──→ [Opera PMS]
      │
      └──→ [Enersis] ──→ [Excel] ──→ [MaintainX]

[MaintainX] ──→ [SAP] (pendiente integración)
```

**Criticidad:** 🔴 Alta
**Frecuencia:** Diaria (múltiples veces)
**Manual/Automático:** Mayormente manual
**Pain Points:**
- Doble/triple entrada de datos
- Falta de sistema integrado CMMS
- Dependencia de Excel como hub central

---

#### Ecosistema de Restaurantes (Bolivian Foods)
```
[POS Simphony/Micros] ──→ [Deliverect] ──→ [Agregadores]
      │
      └──→ [Satcom/SAP] ──→ [Contabilidad]

[Centro Producción] ──→ [SAP] ──→ [Restaurantes]
```

**Criticidad:** 🔴 Alta
**Frecuencia:** Diaria/continua
**Manual/Automático:** Semi-automático
**Pain Points:**
- Falta de control de stock integrado
- Excel paralelo para control de inventarios
- Diferencias entre ventas y facturación

---

#### Ecosistema de Tickets & Soporte
```
[Sistema de monitoreo] ──→ [Jira Service Management]
      │
      ├──→ [Power Automate] ──→ [Jira Service Management]
      │
      └──→ [Jira Service Management] (documentación)
```

**Criticidad:** 🟠 Media
**Frecuencia:** Diaria
**Manual/Automático:** Semi-automático

---

### 4.2. FLUJOS DE REPORTERÍA & BI

#### Flujo de Reportes Ejecutivos
```
[SAP] ────────┐
[Opera] ──────┤
[Simphony] ───┤──→ [Excel consolidación] ──→ [PowerPoint] ──→ [Directorio]
[Bancos] ─────┤
[Proveedores]─┘

[GuestVoice] ──→ [Excel] ──→ [MGS Dashboard]
```

**Criticidad:** 🔴 Alta
**Frecuencia:** Mensual (+ ad-hoc)
**Manual/Automático:** Altamente manual
**Pain Points:**
- 5-10 horas mensuales consolidando información
- Múltiples fuentes de datos
- Falta de DATAWAREHOUSE

---

#### Flujo de Análisis de Costos (F&B)
```
[Simphony ventas] ──→ [Excel] ──→ [Análisis costos]
      │
      └──→ [SAP compras] ──→ [Excel] ──→ [Costeo platos]
            │
            └──→ [Recetas base] ──→ [Excel]
```

**Criticidad:** 🔴 Alta
**Frecuencia:** Diaria/Semanal
**Manual/Automático:** Manual
**Pain Points:**
- Falta de sistema especializado food costing
- Dificultad para estandarizar recetas

---

### 4.3. FLUJOS DE COMUNICACIÓN & COORDINACIÓN

#### Coordinación Operativa (Los Tajibos)
```
[WhatsApp] ──→ [Teams] ──→ [Opera] ──→ [Housekeeping/Mantenimiento]
      │
      └──→ [Outlook] ──→ [Jira] (IT)
```

**Criticidad:** 🟠 Media-Alta
**Frecuencia:** Continua
**Manual/Automático:** Manual
**Pain Points:**
- Múltiples canales generan confusión
- Falta de trazabilidad de solicitudes

---

#### Flujo de Compras & Aprobaciones
```
[Solicitante] ──→ [WhatsApp/Email] ──→ [SAP solicitud] ──→ [Aprobación] ──→ [SAP orden de compra]
      │
      └──→ [Excel seguimiento] ──→ [Proveedor] ──→ [SAP recepción]
```

**Criticidad:** 🔴 Alta
**Frecuencia:** Diaria
**Manual/Automático:** Semi-manual
**Pain Points:**
- Proceso de aprobación lento
- Múltiples firmas requeridas
- Falta de sistematización de solicitudes

---

## 5. MATRIZ DE ROLES Y RESPONSABILIDADES

### 5.1. EMPLEADOS POR EMPRESA

#### 🏨 LOS TAJIBOS (1 empleado entrevistado)
| Empleado | Área/Puesto (inferido) | Sistemas Principales |
|----------|------------------------|----------------------|
| Marcia Gaby Coimbra Noriega | Gerencia/Operaciones | Opera, SAP, Excel |

*Nota: Se infieren múltiples roles adicionales por los procesos mencionados (Mantenimiento, Housekeeping, F&B, TI, Front Desk)*

---

#### 🍔 BOLIVIAN FOODS (9 empleados)
| Empleado | Área/Puesto | Sistemas Principales | Procesos Clave |
|----------|-------------|----------------------|----------------|
| **Fabian Doria Medina** | Gerencia General / Directorio | PowerPoint, Excel, SAP | Presentaciones Directorio, Planificación Estratégica |
| **Alejandra Flores** | Contabilidad | SAP, Excel | Estados Financieros |
| **Micaela Gonzales** | Contabilidad | SAP, Excel | Estados Financieros |
| **Luis La Fuente** | Tesorería | SAP, Bancos | Gestión de tesorería y contabilidad |
| **Carla Flores** | (Área no especificada) | SAP, Excel | - |
| **Carlos Camacho** | (Área no especificada) | SAP, Excel | - |
| **Danny Pinaya** | (Área no especificada) | SAP, Excel | - |
| **Mauricio Clavijo** | (Área no especificada) | SAP, Excel | - |
| **Sissy Fernandez** | (Área no especificada) | SAP, Excel | - |

---

#### 🏢 COMVERSA (7 empleados)
| Empleado | Área/Puesto | Sistemas Principales | Procesos Clave |
|----------|-------------|----------------------|----------------|
| **Samuel Doria Medina Auza** | CEO / Directorio | PowerPoint, Excel, SAP | Evaluación nuevos emprendimientos, Estrategia |
| **Juan Jose Castellon** | Auditoría Interna | SAP, Excel, Documentación | Planificación y Ejecución de Auditoría |
| **Camila Roca** | Análisis de Datos / BI | Excel, DATAWAREHOUSE, BI | Análisis estratégico de información |
| **Gabriela Loza** | Análisis de Datos / BI | Excel, DATAWAREHOUSE, BI | Análisis estratégico de información |
| **Nicolas Monje** | Desarrollo de Software / TI | Visual Studio, Node.js, Angular, Flutter, Docker, GitHub | Desarrollo de software |
| **Gonzalo Cadena** | (Área no especificada) | - | - |
| **Luis Nogales** | (Área no especificada) | - | - |

---

### 5.2. ROLES ORGANIZACIONALES INFERIDOS (Cross-Company)

#### Operaciones
- **Gerente de Operaciones**: Supervisión general, coordinación entre áreas
- **Jefe de Turno**: Operación diaria, resolución de incidencias
- **Supervisor de Área**: Control de calidad, supervisión de equipo
- **Personal Operativo**: Ejecución de tareas operativas

#### Mantenimiento & Ingeniería
- **Jefe de Mantenimiento**: Planificación, gestión de equipo, compras de repuestos
- **Supervisor de Mantenimiento**: Coordinación de trabajos, seguimiento
- **Técnicos de Mantenimiento**: Ejecución de mantenimiento preventivo y correctivo
- **Ingeniero de Planta**: Sistemas críticos, proyectos de mejora

#### Tecnología de la Información
- **Gerente de TI**: Estrategia tecnológica, gestión de equipo
- **Desarrolladores**: Desarrollo de software, integración de sistemas
- **Soporte Técnico**: Gestión de tickets, soporte a usuarios
- **Administrador de Redes**: Infraestructura, seguridad, monitoreo

#### Finanzas & Contabilidad
- **CFO / Gerente Financiero**: Estrategia financiera, relación con bancos
- **Contador General**: Estados financieros, cumplimiento normativo
- **Tesorero**: Gestión de caja, pagos, inversiones
- **Controller**: Control de costos, análisis de variaciones
- **Analista Contable**: Registros contables, conciliaciones
- **Cuentas por Pagar**: Procesamiento de facturas, pagos a proveedores
- **Cuentas por Cobrar**: Facturación, seguimiento de cobros

#### Compras & Logística
- **Jefe de Compras**: Negociación con proveedores, aprobaciones
- **Comprador**: Cotizaciones, órdenes de compra
- **Jefe de Almacén**: Control de inventarios, despachos
- **Almacenero**: Recepción, almacenamiento, distribución

#### Ventas & Comercial
- **Gerente Comercial**: Estrategia de ventas, clientes clave
- **Ejecutivo de Ventas B2B**: Ventas corporativas
- **Coordinador de Eventos**: Cotizaciones, ejecución de eventos
- **Atención al Cliente**: Resolución de quejas, seguimiento

#### Alimentos & Bebidas (Hotelería/Restaurantes)
- **Chef Ejecutivo**: Menús, recetas, estándares de calidad
- **Jefe de Cocina**: Operación diaria de cocina
- **Gerente de A&B**: Control de costos, rentabilidad
- **Controller de A&B**: Análisis de costos, inventarios

#### Housekeeping (Hotelería)
- **Gerente de Pisos**: Gestión del departamento, estándares
- **Supervisor de Housekeeping**: Inspección de habitaciones, coordinación
- **Camarista**: Limpieza de habitaciones

#### Front Office (Hotelería)
- **Gerente de Front Office**: Operación de recepción
- **Recepcionista**: Check-in/out, atención a huéspedes
- **Concierge**: Servicios especiales, información

#### Recursos Humanos
- **Gerente de RRHH**: Gestión de personal, clima laboral
- **Reclutamiento**: Contratación de personal
- **Capacitación**: Inducción, formación continua
- **Nómina**: Procesamiento de sueldos

#### Auditoría & Cumplimiento
- **Auditor Interno**: Planificación y ejecución de auditorías
- **Legal/Compliance**: Cumplimiento normativo
- **Seguridad Industrial**: Prevención de riesgos laborales

#### Proyectos & Desarrollo
- **Gerente de Proyectos**: Planificación, ejecución, control de proyectos
- **Jefe de Obras**: Construcción, desarrollo de locales
- **Diseñador/Arquitecto**: Diseño técnico

---

## 6. MAPEO PROCESO-SISTEMA-PERSONA

### 6.1. PROCESOS FINANCIEROS

#### Elaboración de Estados Financieros (Mensual)
**Sistemas:**
- SAP (fuente principal)
- Excel (consolidación y análisis)
- CMNet (legacy, hasta migración)

**Personal Involucrado:**
- Contador General: Alejandra Flores, Micaela Gonzales (Bolivian Foods)
- Equipo de Contabilidad
- CFO/Gerente Financiero (revisión)

**Flujo:**
```
[SAP extractos] → [Excel ajustes] → [Revisión] → [Estados Financieros] → [Directorio]
```

**Pain Points:**
- Entrega tardía de información de otras áreas
- Proceso manual de consolidación
- CMNet aún en uso durante migración

---

#### Conciliación Bancaria (Mensual)
**Sistemas:**
- SAP
- Portales bancarios
- Excel

**Personal:**
- Tesorería: Luis La Fuente
- Contabilidad

**Flujo:**
```
[Extractos bancarios] → [SAP registros] → [Conciliación en Excel] → [Ajustes SAP]
```

---

#### Proceso de Pago a Proveedores (Diario)
**Sistemas:**
- SAP (solicitud y registro)
- Excel (seguimiento)
- WhatsApp (comunicación)
- Portales bancarios (ejecución)

**Personal:**
- Solicitante (cualquier área)
- Aprobador (Gerente de área)
- Cuentas por Pagar
- Tesorero

**Flujo:**
```
[Solicitud] → [SAP aprobación] → [Programación pago] → [Ejecución bancaria] → [Registro SAP]
```

**Pain Points:**
- Múltiples firmas requeridas
- Proceso de aprobación lento
- Falta de visibilidad del estado

---

### 6.2. PROCESOS OPERATIVOS (LOS TAJIBOS)

#### Check-In de Huéspedes (Diario)
**Sistemas:**
- Opera PMS (principal)
- Control Panel (llaves)
- Móvil Key (app huéspedes)
- Marriott platforms (validación reservas)

**Personal:**
- Recepcionista
- Supervisor de Front Office

**Flujo:**
```
[Reserva] → [Verificación Opera] → [Registro] → [Asignación habitación] → [Emisión llave] → [Bienvenida]
```

---

#### Gestión de Mantenimiento Correctivo (Diario)
**Sistemas:**
- WhatsApp (solicitud)
- MaintainX (registro y seguimiento)
- Excel (respaldo/análisis)
- Opera PMS (cierre orden habitación)

**Personal:**
- Solicitante (cualquier área)
- Jefe de Mantenimiento
- Técnico asignado
- Supervisor

**Flujo:**
```
[WhatsApp solicitud] → [MaintainX orden trabajo] → [Asignación técnico] → [Ejecución] → [Cierre MaintainX] → [Cierre Opera (si habitación)]
```

**Pain Points:**
- Solicitudes por múltiples canales
- Doble registro (WhatsApp + MaintainX)
- Falta de integración con Opera

---

#### Supervisión de Eventos (Diario)
**Sistemas:**
- Opera (reserva y facturación)
- Excel (planificación y costeo)
- Teams/WhatsApp (coordinación)
- SAP (compras de insumos)

**Personal:**
- Coordinador de Eventos
- Chef/Cocina
- Gerente de A&B
- Housekeeping (montaje)
- Mantenimiento (soporte)

**Flujo:**
```
[Cotización] → [Aprobación cliente] → [Orden servicio Opera] → [Comunicación áreas] → [Ejecución evento] → [Facturación] → [Cierre]
```

**Pain Points:**
- Revisión y corrección repetida de órdenes de servicio
- Falta de alineación entre departamentos
- Comunicación por múltiples canales

---

### 6.3. PROCESOS DE RESTAURANTES (BOLIVIAN FOODS)

#### Monitoreo de Ventas (Diario/Semanal)
**Sistemas:**
- Simphony/Micros (POS)
- Deliverect (delivery apps)
- SAP (consolidación)
- Excel (análisis)

**Personal:**
- Gerente de Operaciones
- Gerente de Tienda
- Controller

**Flujo:**
```
[Ventas POS] → [Deliverect agregación] → [SAP ventas] → [Excel dashboard] → [Análisis] → [Acciones]
```

**Pain Points:**
- Diferencias entre facturación y ventas totales
- Falta de control de stock en sistema
- Excel pesado y lento

---

#### Cálculo de Costo de Ventas (Mensual)
**Sistemas:**
- SAP (compras y ventas)
- Simphony (ventas detalle)
- Excel (cálculo)
- Recetas base

**Personal:**
- Controller de A&B
- Contabilidad
- Chef (validación recetas)

**Flujo:**
```
[SAP compras] → [Inventario inicial] → [Inventario final] → [Excel cálculo] → [Análisis variaciones] → [Ajustes]
```

**Pain Points:**
- Dificultad para estandarizar recetas
- Proceso burocrático para ajustes
- Falta de sistema especializado food costing

---

### 6.4. PROCESOS CORPORATIVOS (COMVERSA)

#### Análisis Estratégico de Información (Semanal)
**Sistemas:**
- Excel (principal)
- DATAWAREHOUSE (proyecto)
- Hadoop DB, MySQL, MariaDB (fuentes)
- Power BI (inferido)

**Personal:**
- Camila Roca (Analista)
- Gabriela Loza (Analista)
- Gerencia/Directorio (receptores)

**Flujo:**
```
[Múltiples fuentes datos] → [Extracción] → [Excel consolidación] → [Análisis] → [Dashboard/Reporte] → [Insights]
```

**Pain Points:**
- Análisis manual de desviaciones y errores
- Falta de acceso directo a bases de datos
- Tareas repetitivas de actualización de conexiones
- Falta de DATAWAREHOUSE centralizado

---

#### Desarrollo de Software (Diario)
**Sistemas:**
- Visual Studio/Visual Code
- Node.js, Angular, Flutter
- GitHub (control versiones)
- Docker (contenedores)
- SQL Server, MySQL, MariaDB, Hadoop DB

**Personal:**
- Nicolas Monje (Developer)
- Equipo de Desarrollo
- Gerente de TI

**Flujo:**
```
[Requerimiento] → [Diseño] → [Desarrollo] → [GitHub commit] → [Testing] → [Deploy Docker] → [Producción]
```

---

#### Auditoría Interna (Según requerimiento)
**Sistemas:**
- SAP (fuente principal)
- Excel (papeles de trabajo)
- Microsoft Office (informes)
- Documentación física y digital

**Personal:**
- Juan Jose Castellon (Auditor Interno)
- Equipo de Auditoría
- Áreas auditadas

**Flujo:**
```
[Plan Anual] → [Alcance auditoría] → [Ejecución] → [Hallazgos] → [Informe] → [Seguimiento]
```

---

## 7. CONCLUSIONES Y RECOMENDACIONES

### 7.1. Hallazgos Principales

1. **Excel como Sistema Central No Oficial**
   - Más de 100 menciones en flujos de datos
   - Usado para compensar falta de integración entre sistemas
   - Genera retrabajos y riesgo de errores

2. **Falta de Integración SAP-Opera-POS**
   - Conciliaciones manuales diarias (1-2 horas)
   - Múltiples fuentes de verdad
   - Diferencias requieren investigación manual

3. **Comunicación por Múltiples Canales**
   - WhatsApp, Teams, Outlook, presencial
   - Falta de trazabilidad
   - Pérdida de información

4. **Procesos de Aprobación Lentos**
   - Múltiples firmas requeridas
   - Falta de workflows automatizados
   - Genera delays operativos

5. **Dependencia de Personas Clave**
   - Conocimiento crítico no documentado
   - Falta de respaldos para roles clave
   - Riesgo operacional

---

### 7.2. Oportunidades de Mejora Prioritarias

#### 🔴 Prioridad Crítica
1. **Integración SAP-Opera-Simphony-Satcom**
   - Eliminar conciliaciones manuales
   - Integración en tiempo real
   - Impacto: 2-4 horas diarias recuperadas

2. **Sistema CMMS Integrado (MaintainX ← → SAP)**
   - Eliminar doble entrada de datos
   - Workflow de aprobación automatizado
   - Impacto: 40-60% reducción tiempo coordinación

3. **Automatización de Aprobaciones**
   - Workflow digital para solicitudes de pago
   - Workflow para órdenes de compra
   - Notificaciones automáticas
   - Impacto: 50% reducción en tiempo de aprobación

#### 🟠 Prioridad Alta
4. **Implementación DATAWAREHOUSE**
   - Centralización de fuentes de datos
   - Reducción de Excel como hub
   - Self-service BI
   - Impacto: 80-90% reducción en tiempo de reportería

5. **CRM Funcional (Bolivian Foods)**
   - Gestión de clientes corporativos
   - Seguimiento de cotizaciones
   - Pipeline de ventas
   - Impacto: Mejora en conversión y seguimiento

6. **Sistema de Food Costing**
   - Estandarización de recetas
   - Costeo automático de platos
   - Control de márgenes en tiempo real
   - Impacto: 3-5% mejora en márgenes

#### 🟡 Prioridad Media
7. **Unificación de Comunicación Operativa**
   - Canal único para solicitudes (app móvil o portal)
   - Trazabilidad de requerimientos
   - SLA tracking
   - Impacto: Mejora en respuesta y accountability

8. **Portal de Autoservicio para Empleados**
   - Solicitud de permisos
   - Consulta de información (recibos, vacaciones)
   - Capacitaciones
   - Impacto: Reducción carga RRHH

---

### 7.3. Roadmap de Implementación Sugerido

**Fase 1 (0-6 meses) - Quick Wins:**
- Automatización aprobaciones (workflows Power Automate/SAP)
- Estandarización de canal de comunicación operativa
- Capacitación en herramientas existentes (MaintainX, Jira)

**Fase 2 (6-12 meses) - Integraciones Core:**
- Integración SAP-Opera-Simphony
- Implementación CRM
- Sistema CMMS integrado completo

**Fase 3 (12-18 meses) - Transformación Digital:**
- DATAWAREHOUSE y BI self-service
- Sistema Food Costing
- Portal de autoservicio empleados
- Migración completa de CMNet a SAP

**Fase 4 (18-24 meses) - Optimización & Analytics:**
- Advanced analytics & IA
- Automatizaciones con RPA
- Predictive maintenance
- Dynamic pricing (F&B)

---

## 8. ANEXOS

### Anexo A: Glosario de Sistemas
*(Ya incluido en sección 3)*

### Anexo B: Convenciones de Nomenclatura
- **[Sistema]**: Nombre de sistema tecnológico
- **{Proceso}**: Nombre de proceso de negocio
- *Empleado*: Persona entrevistada o mencionada

### Anexo C: Fuentes de Información
- 44 entrevistas a personal clave (2024-2025)
- 1,743 entidades consolidadas con IA
- Consenso: 100% (consensus_confidence = 1.0)
- Método: Análisis de lenguaje natural con validación cruzada

---

**Documento generado automáticamente por sistema RAG-Comversa**
**Para consultas sobre este análisis contactar a:** [Equipo de Análisis]
**Próxima actualización:** Ingesta de nuevas entrevistas o cambios significativos en procesos

---

*Fin del documento*
