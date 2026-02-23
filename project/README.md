IECGGS: Índice de Engagement y Contribución a la Gobernanza Global de la Salud

Descripción
- Índice formativo que mide inputs y comportamientos de los Estados hacia la gobernanza global de la salud como CAS.
- Dimensiones: A) Engagement regulatorio (SPAR/RSI), B) Esfuerzo doméstico en salud (CHE%PIB, UHC, política/plan/estrategia, reconocimiento del derecho a la salud), C) Participación institucional y decisoria (WHA), D) Ruptura de reglas/sanción (Art. 7).

Arquitectura (módulos)
- M0 Ingesta y estandarización
- M1 Construcción de dimensiones (derivaciones y agregaciones por dimensión)
- M2 Normalización (min–max a 0–1; discretas 0/1/2 → 0/0.5/1)
- M3 Agregación (subíndices y índice global)
- M4 Penalización y sensibilidad (Art.7; λ∈{0.1,0.25,0.5})

Datos de entrada esperados (en /workspace/files)
- SPAR (A_e-SPAR.xlsx) u hoja con columnas como "ISO Code" y "Promedio total"
- CHE%PIB (B_health_expenditure_GDP.csv) con indicador "Current health expenditure ..."
- UHC Service Coverage Index (B_UHCIndex.csv) con indicador que contenga "UHC" e "index"
- Política/Plan/Estrategia UHC (B_national health policy/plan/strategy.csv)
- Reconocimiento del derecho a la salud (B_recognition.csv)
- Exclusiones Art.7 (C_Exclusiones.xlsx) con columnas Año y País
- Participación WHA (C_Particip.xlsx) con columnas WHA/Año/Actividad/País

Salidas (en /workspace/project/outputs)
- panel_clean.csv (panel país–año con todas las variables limpias)
- subindices.csv (E_reg, E_dom, E_part)
- IECGGS_raw.csv
- IECGGS_penalized.csv (λ=0.1,0.25,0.5)
- sensitivity.csv (grid de λ y esquemas de pesos)
- data_dictionary.md
- panel_with_flags.csv (panel con flags de elegibilidad por pilar e índice)
- coverage_report_by_variable.csv / by_country / by_year / by_pillar
- coverage_summary.md


Reglas de elegibilidad (codificadas)
- E_reg se calcula si `n_reg_obs >= 1`.
- E_dom se calcula si `n_dom_obs >= 3`.
- E_part se calcula si `n_part_obs >= 2`.
- IECGGS_raw se calcula si `n_pillars_ok >= 3`.
- Umbrales configurables por variables de entorno: `IECGGS_MIN_REG_OBS`, `IECGGS_MIN_DOM_OBS`, `IECGGS_MIN_PART_OBS`, `IECGGS_MIN_INDEX_PILLARS`.

Ejecución
- ./entrypoint.sh ejecuta el pipeline end-to-end y deja las salidas en outputs/.
- Entornos sin red/proxy: el entrypoint evita depender de `pip` online por defecto; intenta instalar sólo desde wheelhouse local (`LOCAL_WHEELHOUSE`, por defecto `/workspace/wheels`).
- Fallback online opcional: definir `ALLOW_ONLINE_INSTALL=1` para habilitar `pip install` contra internet/proxy cuando esté disponible.

Notas metodológicas clave
- No se usa World Power Index, GHS u otros índices como inputs. Pueden usarse luego para validación/contraste.
- No se entrena ni predice: es construcción de índice formativo con validaciones internas.

Licencia y orígenes
- Código original de este proyecto. Los datos provienen de los archivos suministrados por el usuario.
