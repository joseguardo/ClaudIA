# ClaudIA: ClaudIA: Desarrollo de funcionalidades mediante inteligencia artificial orientadas al Contract Life Management (CLM) y a la anonimización de datos sensibles

Este repositorio contiene los códigos más importantes de ambos módulos de mi Trabajo de Fin de Grado de GITT.
## CLM (Contract Life Manager)
Por una parte, se pueden encontrar en la carpeta CLM todos los archivos que contienen la lógica de generación del Knowledge Graph así como de la RAG Pipeline compuesta por un retriever, un generator y un verifier. 
Además se puede encontrar un ejemplo de calendario contractual generado en formato html y en formato json para visualizar el resultado. 
## Anonimizador 
Por otra parte, contiene la lógica de detección así como las plantillas de prompts que llevan a la anonimización de documentos. 
Como mencionado en la memoria, estos archivos están desplegados en AWS y se ejecutan haciendo uso de AWS BedRock cuando la API desplegada recibe una petición desde el AddIn de Word. 

