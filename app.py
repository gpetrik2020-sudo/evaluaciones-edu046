import os
import json
from flask import Flask, render_template, abort, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────
# RAG — contexto semántico por semana (clon de backbone-edu046)
# ─────────────────────────────────────────────────────────────
RAG = {
    "s1": {
        "1.1": "El mercado es una construcción operativa emergente de dispositivos, actores y transacciones, no una entidad empírica pre-existente.",
        "1.2": "La incertidumbre es la materia prima del sistema de investigación: no se elimina, se redistribuye.",
        "1.3": "La investigación de mercados es un sistema: sus componentes se retroalimentan y la salida depende de la arquitectura completa.",
    },
    "s2": {
        "2.1": "Definir el problema es una decisión arquitectónica que estructura todo lo que sigue — quién lo define determina qué puede encontrarse.",
        "2.2": "El problema se construye, no se descubre: implica seleccionar, enmarcar y reducir la complejidad desde una posición.",
        "2.3": "El sesgo puede introducirse desde el planteamiento: en la elección del problema, la perspectiva del cliente y los supuestos implícitos.",
    },
    "s3": {
        "3.1": "Operacionalizar es traducir experiencias en variables: ese proceso implica pérdidas y decisiones teóricas.",
        "3.2": "Los instrumentos producen el dato que miden: son dispositivos ontológicos, no espejos.",
        "3.3": "El dato es un artefacto construido, no un hecho bruto: lleva inscrita la teoría y el método que lo produjeron.",
    },
    "s4": {
        "4.1": "Lo cualitativo produce interpretación densa: significado, contexto, proceso.",
        "4.2": "Lo cuantitativo formaliza: convierte fenómenos en variables medibles con supuestos sobre su estructura.",
        "4.3": "Triangular no garantiza mayor verdad: la convergencia de métodos distintos puede confirmar un mismo sesgo.",
    },
    "s5": {
        "5.1": "El dato no habla: demanda un lector con un marco. La interpretación no es opcional, es constitutiva.",
        "5.2": "Un modelo es una simplificación útil. Su valor no está en representar la realidad sino en facilitar decisiones.",
        "5.3": "Segmentar es imponer distinciones al continuo del mercado. La segmentación válida es la que opera.",
    },
    "s6": {
        "6.1": "Decidir sin certeza es la condición normal. La investigación gestiona esa incertidumbre, no la resuelve.",
        "6.2": "La investigación como tecnología: transforma incertidumbre en información procesable para decisiones.",
        "6.3": "La ética no es un anexo: es constitutiva del proceso de investigación. Investigar es intervenir.",
    },
}

# ─────────────────────────────────────────────────────────────
# PREGUNTAS — 10 por semana
# ─────────────────────────────────────────────────────────────
PREGUNTAS = {
    "s1": [
        "¿Por qué el mercado es una construcción operativa y no una entidad empírica?",
        "Explica qué papel juega la incertidumbre como materia prima del sistema de investigación.",
        "¿Cómo distingues entre un mercado como fenómeno y un mercado como dispositivo?",
        "¿Qué significa que la investigación de mercados sea un 'sistema' en sentido estricto?",
        "Describe la relación entre decisión e incertidumbre en el contexto de la investigación.",
        "¿Qué implica operativamente construir un mercado? Da un ejemplo concreto.",
        "¿Cuál es la diferencia entre reducir incertidumbre y eliminarla en la práctica?",
        "Explica cómo los actores que participan en un mercado contribuyen a su construcción.",
        "¿Qué elementos hacen que la investigación funcione como sistema y no como proceso lineal?",
        "¿Por qué es problemático asumir que los mercados 'existen' antes de ser investigados?",
    ],
    "s2": [
        "¿Quién tiene autoridad para definir el problema de investigación y qué implica esa decisión?",
        "Explica cómo la arquitectura de investigación determina qué preguntas son posibles.",
        "¿Qué es el 'sesgo de planteamiento' y cómo puede introducirse desde el inicio de un estudio?",
        "Describe el proceso de construcción de un problema de investigación válido.",
        "¿Cómo se diferencia un problema bien formulado de uno mal planteado?",
        "¿Por qué el problema no es un simple punto de partida sino una decisión arquitectónica?",
        "Explica la relación entre quién financia la investigación y cómo se construye el problema.",
        "¿Qué sesgos estructurales pueden afectar el planteamiento en investigación de mercados?",
        "¿Cómo puede un investigador detectar y corregir el sesgo en la definición del problema?",
        "¿Qué diferencia existe entre un problema operativo y uno de investigación epistemológicamente?",
    ],
    "s3": [
        "¿Cómo se transforma una experiencia observable en una variable medible?",
        "Explica por qué los instrumentos de investigación no son neutrales sino que producen realidad.",
        "¿Qué significa que el dato sea un 'artefacto' y no un reflejo de la realidad?",
        "Describe el proceso de operacionalización: de la experiencia a la variable.",
        "¿Qué criterios definen si un instrumento de medición es válido para una investigación?",
        "¿Cómo afecta el diseño del instrumento a la calidad de los datos obtenidos?",
        "Explica la diferencia entre un dato bruto y un dato procesado epistemológicamente.",
        "¿Por qué la elección de variables implica ya una posición teórica?",
        "¿Qué riesgos epistemológicos tiene tratar los datos como si fueran hechos objetivos?",
        "Describe cómo el instrumento y el dato están mutuamente constituidos en una investigación.",
    ],
    "s4": [
        "¿Qué tipo de conocimiento produce la investigación cualitativa que no produce la cuantitativa?",
        "¿Cómo funciona la formalización en la investigación cuantitativa y qué supuestos implica?",
        "¿Qué significa triangular métodos y cuándo es epistemológicamente válido hacerlo?",
        "Explica la diferencia entre complementariedad y equivalencia en el uso de métodos mixtos.",
        "¿Cuáles son los límites de la interpretación en la investigación cualitativa?",
        "¿Qué riesgos tiene convertir fenómenos cualitativos en variables cuantitativas?",
        "Describe una situación en la que la triangulación metodológica sea indispensable.",
        "¿Por qué no toda convergencia de métodos implica mayor validez?",
        "¿Cómo afecta la perspectiva del investigador la interpretación de datos cualitativos?",
        "Explica qué aporta cada tipo de investigación al problema de la representatividad.",
    ],
    "s5": [
        "¿Por qué se afirma que el dato 'no habla' y necesita ser interpretado?",
        "Explica qué función cumple un modelo en la simplificación de la realidad.",
        "¿Qué criterios permiten distinguir una buena segmentación de una arbitraria?",
        "¿Cuál es el riesgo de confundir el modelo con la realidad que modela?",
        "Describe el proceso de interpretación desde la lectura de datos hasta la conclusión.",
        "¿Cómo influye el marco teórico en la interpretación de los resultados?",
        "¿Qué hace válida a una segmentación en términos operativos y estratégicos?",
        "Explica la diferencia entre describir patrones y explicar causas en el análisis de datos.",
        "¿Qué significa que un modelo sea una simplificación útil y no una representación exacta?",
        "¿Cómo puede la segmentación distorsionar la comprensión del mercado si se aplica mal?",
    ],
    "s6": [
        "¿Qué implica tomar decisiones 'sin certeza' y cómo la investigación gestiona ese riesgo?",
        "Explica cómo la investigación de mercados funciona como tecnología de reducción de incertidumbre.",
        "¿Cuáles son las implicaciones éticas de intervenir en un mercado a partir de investigación?",
        "¿Qué responsabilidades tiene el investigador cuando sus resultados afectan a comunidades?",
        "¿Cómo se relacionan las dimensiones técnica y ética en el diseño de una investigación?",
        "Explica qué significa que la investigación sea una forma de intervención y no solo de observación.",
        "¿Qué criterios éticos deben guiar el uso de datos en investigación de mercados?",
        "¿Cómo puede la tecnología amplificar tanto las capacidades como los riesgos éticos?",
        "Describe una situación en la que una decisión basada en datos sea técnicamente correcta pero éticamente problemática.",
        "¿Por qué la ética en la investigación de mercados no es opcional sino estructural al proceso?",
    ],
}

# ─────────────────────────────────────────────────────────────
# EXÁMENES — 3 parciales + 1 final
# Pesos: 20% + 15% + 15% + 50% = 100%
# ─────────────────────────────────────────────────────────────
EXAMENES = {
    "parcial1": {
        "titulo":   "Examen Parcial 1",
        "semanas":  ["s1", "s2"],
        "peso":     20,
        "unidades": "Unidades 1 y 2 — El mercado y el problema de investigación",
        "preguntas": PREGUNTAS["s1"][:5] + PREGUNTAS["s2"][:5],
    },
    "parcial2": {
        "titulo":   "Examen Parcial 2",
        "semanas":  ["s3", "s4"],
        "peso":     15,
        "unidades": "Unidades 3 y 4 — Variables, instrumentos y métodos",
        "preguntas": PREGUNTAS["s3"][:5] + PREGUNTAS["s4"][:5],
    },
    "parcial3": {
        "titulo":   "Examen Parcial 3",
        "semanas":  ["s5", "s6"],
        "peso":     15,
        "unidades": "Unidades 5 y 6 — Análisis, decisión y ética",
        "preguntas": PREGUNTAS["s5"][:5] + PREGUNTAS["s6"][:5],
    },
    "final": {
        "titulo":   "Examen Final",
        "semanas":  ["s1", "s2", "s3", "s4", "s5", "s6"],
        "peso":     50,
        "unidades": "Unidades 1–6 — Curso completo EDU046",
        "preguntas": [
            PREGUNTAS["s1"][0], PREGUNTAS["s1"][5],
            PREGUNTAS["s2"][0], PREGUNTAS["s2"][5],
            PREGUNTAS["s3"][0], PREGUNTAS["s3"][5],
            PREGUNTAS["s4"][0], PREGUNTAS["s4"][5],
            PREGUNTAS["s5"][0], PREGUNTAS["s6"][8],
        ],
    },
}

# ─────────────────────────────────────────────────────────────
# RUTAS
# ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('lista_examenes.html', examenes=EXAMENES)


@app.route('/examen')
def lista_examenes():
    return render_template('lista_examenes.html', examenes=EXAMENES)


@app.route('/examen/<examen_id>')
def examen(examen_id):
    ex = EXAMENES.get(examen_id)
    if not ex:
        abort(404)
    return render_template('examen.html', ex=ex, examen_id=examen_id)


@app.route('/calificar_examen', methods=['POST'])
def calificar_examen():
    data       = request.get_json()
    examen_id  = data.get('examen_id', 'parcial1')
    estudiante = data.get('estudiante', 'Estudiante')
    respuestas = data.get('respuestas', [])

    ex = EXAMENES.get(examen_id)
    if not ex:
        return jsonify({'error': 'Examen no encontrado'}), 404

    # RAG combinado de las semanas del examen
    rag_combinado = {sid: RAG.get(sid, {}) for sid in ex['semanas']}

    prompt = f"""Eres un evaluador académico experto en investigación de mercados constructivista.

EXAMEN: {ex['titulo']}
UNIDADES: {ex['unidades']}

RAG DEL CURSO (contexto semántico de las unidades evaluadas):
{json.dumps(rag_combinado, ensure_ascii=False)}

PREGUNTAS ({len(ex['preguntas'])} preguntas, 10 puntos cada una):
{json.dumps(ex['preguntas'], ensure_ascii=False)}

RESPUESTAS DEL ESTUDIANTE ({estudiante}):
{json.dumps(respuestas, ensure_ascii=False)}

Evalúa cada respuesta del 0 al 10.
Criterios: profundidad conceptual, uso del lenguaje del curso, coherencia argumentativa, ejemplos concretos.

Responde ÚNICAMENTE en JSON válido con esta estructura exacta:
{{
  "estudiante": "{estudiante}",
  "examen": "{ex['titulo']}",
  "peso_porcentual": {ex['peso']},
  "resultados": [
    {{
      "pregunta": 1,
      "score": 0,
      "comentario": "comentario breve (máx 60 palabras)",
      "nivel": "insuficiente|básico|competente|destacado"
    }}
  ],
  "resumen": {{
    "total": 0,
    "promedio": 0.0,
    "calificacion_ponderada": 0.0,
    "fortalezas": "texto breve",
    "areas_mejora": "texto breve",
    "diagnostico": "diagnóstico de 2-3 oraciones del perfil conceptual del estudiante"
  }}
}}"""

    try:
        client   = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2500,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)

        scores    = [r['score'] for r in result['resultados']]
        promedio  = round(sum(scores) / len(scores), 1)
        ponderada = round((promedio / 10) * ex['peso'], 2)

        result['resumen']['total']                  = sum(scores)
        result['resumen']['promedio']               = promedio
        result['resumen']['calificacion_ponderada'] = ponderada
        result['resumen']['peso_porcentual']        = ex['peso']

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
