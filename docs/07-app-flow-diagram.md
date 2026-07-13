# Diagrama de flujo completo de JornadaDex

Este documento representa el comportamiento actual de la aplicacion, sus roles y los principales procesos de negocio.

## Flujo general

```mermaid
flowchart TD
    A[Visitante abre JornadaDex] --> B{Tiene sesion activa?}
    B -- No --> C[Landing publica]
    C --> D{Accion}
    D -- Iniciar sesion --> E[Login]
    D -- Registrar empresa --> F[Alta publica]
    D -- Recuperar clave --> G[Recuperacion de contrasena]
    D -- Legales --> H[Privacidad y terminos]

    F --> F1[Validar limite y Turnstile]
    F1 --> F2[Crear empresa y Administrador]
    F2 --> F3{Verificacion de email requerida?}
    F3 -- Si --> F4[Enviar enlace de activacion]
    F4 --> F5[Verificar token]
    F3 -- No --> E
    F5 --> E

    G --> G1[Ingresar usuario o email]
    G1 --> G2[Enviar enlace temporal]
    G2 --> G3[Validar token y vigencia]
    G3 --> G4[Definir nueva clave]
    G4 --> E

    E --> E1{Credenciales validas y cuenta activa?}
    E1 -- No --> E2[Registrar intento fallido]
    E2 --> E
    E1 -- Si --> E3{Email verificado?}
    E3 -- No --> F4
    E3 -- Si --> I[Crear sesion y auditar login]

    B -- Si --> J[Resolver usuario, rol y empresa activa]
    I --> J
    J --> K{Rol}

    K -- Colaborador --> L[Dashboard laboral]
    K -- Encargado --> M[Dashboard supervision por defecto]
    M --> M1[Dashboard laboral propio]
    K -- Administrador --> N[Dashboard general de empresa]
    K -- Developer --> O[Administracion de plataforma]

    L --> P[Registrar y consultar horas propias]
    M --> Q[Supervisar colaboradores asignados]
    M1 --> P
    N --> R[Gestion integral de la empresa]
    O --> S[Seleccionar empresa activa]
    S --> T[Gestionar empresas y usuarios]

    P --> U[Reportes y exportacion segun alcance]
    Q --> U
    R --> U
    Q --> V[Colaboradores, clientes, areas y tareas]
    R --> V
    R --> W[Auditoria]

    L --> X[Cerrar sesion]
    M --> X
    N --> X
    O --> X
    X --> E
```

## Registro de horas

```mermaid
flowchart TD
    A[Usuario abre Horas] --> B{Es Developer?}
    B -- Si --> Z[Acceso denegado]
    B -- No --> C[Determinar alcance por rol]
    C --> D[Seleccionar colaborador permitido]
    D --> E[Seleccionar encargado]
    E --> F[Seleccionar cliente]
    F --> G[Seleccionar area]
    G --> H[Cargar tareas del area]
    H --> I[Seleccionar tarea y observaciones]
    I --> J{Datos y relaciones validos?}
    J -- No --> K[Mostrar error]
    K --> D
    J -- Si --> L{Ya tiene otra tarea activa?}
    L -- Si --> M[Solicitar pausar o finalizar la activa]
    M --> A
    L -- No --> N[Crear registro con fecha y hora automaticas]
    N --> O[Estado: en curso]
    O --> P{Accion sobre la tarea}
    P -- Pausar --> Q[Guardar instante de pausa]
    Q --> R[Estado: pausada]
    R --> S{Accion}
    S -- Reanudar --> T[Acumular segundos pausados]
    T --> O
    S -- Finalizar --> U[Calcular horas sin pausas]
    P -- Finalizar --> U
    U --> V[Guardar hora final y total]
    V --> W[Estado: finalizada]
    W --> X[Actualizar dashboards y reportes]

    P -- Editar --> Y{Es Encargado o Administrador?}
    Y -- Si --> Y1[Modificar empleado, encargado, cliente, area o tarea]
    Y1 --> Y2[Agregar nota y auditar cambio]
    Y -- No --> Z1[Acceso denegado]

    P -- Eliminar --> AA{Tiene permiso sobre el registro?}
    AA -- Si --> AB[Eliminacion logica y auditoria]
    AA -- No --> Z1
```

## Dashboards y visibilidad

```mermaid
flowchart LR
    A[Registros de tiempo] --> B{Rol actual}

    B -- Colaborador --> C[Unicamente registros propios]
    C --> C1[Tarea en curso]
    C --> C2[Horas hoy, ultimos 7 dias y mes corriente]
    C --> C3[Horas por tarea: semanal y mensual]
    C --> C4[Horas por area: semanal y mensual]
    C --> C5[Horas por cliente: semanal y mensual]

    B -- Encargado --> D[Registros cuyo supervisor_id es el usuario]
    D --> D1[Ranking de colaboradores]
    D --> D2[Horas por tarea]
    D --> D3[Horas por area]
    D --> D4[Horas por cliente]
    D --> D5[Alternar a dashboard laboral propio]

    B -- Administrador --> E[Todos los registros de su empresa]
    E --> E1[Resumen general]
    E --> E2[Ranking de colaboradores]
    E --> E3[Horas por tarea, area y cliente]

    B -- Developer --> F[Empresa elegida en la sesion]
    F --> F1[Administracion de plataforma]

    G[Ultimos 7 dias] --> H[Fecha de referencia menos 6 dias]
    I[Mensual] --> J[Desde el dia 1 del mes corriente]
```

## Gestion de la empresa

```mermaid
flowchart TD
    A[Encargado o Administrador] --> B{Modulo}

    B -- Colaboradores --> C[Listar colaboradores visibles]
    C --> C1[Crear colaborador y usuario]
    C --> C2[Editar datos, rol y acceso]
    C --> C3[Eliminar logicamente]

    B -- Clientes --> D[Listar clientes]
    D --> D1[Crear o editar ficha contable]
    D --> D2[Importar CSV o Excel]
    D --> D3[Descargar plantillas]
    D --> D4[Eliminar logicamente]

    B -- Areas y tareas --> E[Listar catalogo]
    E --> E1[Crear area]
    E --> E2[Crear tarea vinculada a un area]
    E --> E3[Eliminar logicamente area o tarea]
    E --> E4[Entregar tareas por area en JSON]

    B -- Reportes --> F[Aplicar filtros]
    F --> F1[Colaborador]
    F --> F2[Encargado]
    F --> F3[Cliente]
    F --> F4[Area y tarea]
    F --> F5[Rango de fechas]
    F --> G[Ver resultados]
    G --> H[Exportar CSV]
    G --> I[Exportar Excel]

    B -- Auditoria --> J{Es Administrador?}
    J -- Si --> K[Ver actividad y cambios de la empresa]
    J -- No --> L[Acceso restringido]

    C1 --> M[Auditar operacion]
    C2 --> M
    C3 --> M
    D1 --> M
    D2 --> M
    D4 --> M
    E1 --> M
    E2 --> M
    E3 --> M
    H --> M
    I --> M
```

## Administracion de plataforma

```mermaid
flowchart TD
    A[Developer autenticado] --> B[Panel de plataforma]
    B --> C{Accion}
    C -- Empresas --> D[Listar empresas]
    D --> D1[Crear empresa]
    D --> D2[Editar o activar empresa]
    D --> D3[Eliminar empresa]
    D --> D4[Reiniciar actividad]
    C -- Usuarios --> E[Listar usuarios globales]
    E --> E1[Editar usuario, rol y estado]
    E --> E2[Eliminar usuario]
    C -- Trabajar sobre empresa --> F[Seleccionar empresa activa]
    F --> G[Guardar active_company_id en sesion]
    G --> H[Consultar datos de la empresa seleccionada]
```

## Relaciones principales de datos

```mermaid
erDiagram
    COMPANY ||--o{ USER : posee
    COMPANY ||--o{ EMPLOYEE : emplea
    COMPANY ||--o{ AREA : define
    COMPANY ||--o{ ACCOUNTING_CLIENT : atiende
    USER o|--o| EMPLOYEE : representa
    AREA ||--o{ TASK : contiene
    EMPLOYEE ||--o{ TIME_RECORD : registra
    USER ||--o{ TIME_RECORD : supervisa
    ACCOUNTING_CLIENT ||--o{ TIME_RECORD : recibe_horas
    AREA ||--o{ TIME_RECORD : clasifica
    TASK ||--o{ TIME_RECORD : detalla
    COMPANY ||--o{ AUDIT_LOG : conserva
    USER ||--o{ AUDIT_LOG : ejecuta
    USER ||--o{ SECURITY_EVENT : genera
```

## Rutas principales

| Modulo              | Ruta base         | Acceso                                                    |
| ------------------- | ----------------- | --------------------------------------------------------- |
| Landing y dashboard | `/`, `/dashboard` | Publico / autenticado                                     |
| Autenticacion       | `/auth`           | Publico y autenticado para logout                         |
| Horas               | `/time-records`   | Usuarios de empresa                                       |
| Colaboradores       | `/employees`      | Encargado y Administrador                                 |
| Clientes            | `/clients`        | Encargado y Administrador                                 |
| Areas y tareas      | `/areas`          | Lectura autenticada; gestion de Encargado y Administrador |
| Reportes            | `/reports`        | Autenticado, limitado por visibilidad                     |
| Auditoria           | `/audit`          | Administrador                                             |
| Plataforma          | `/platform`       | Developer                                                 |
