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

Ejecución
- ./entrypoint.sh ejecuta el pipeline end-to-end y deja las salidas en outputs/.

Notas metodológicas clave
- No se usa World Power Index, GHS u otros índices como inputs. Pueden usarse luego para validación/contraste.
- No se entrena ni predice: es construcción de índice formativo con validaciones internas.

Licencia y orígenes
- Código original de este proyecto. Los datos provienen de los archivos suministrados por el usuario.
