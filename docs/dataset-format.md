# Formato del dataset

Los XML conservan namespaces y jerarquía y llevan comentario inequívoco. JSON conserva el contrato
de entrada y añade `datasetSanitization`; la proyección de XML usa raíz `{metadata, cfdi}`. El hash
publicado se calcula después de sanitizar y nunca se copia `sourceHash`. El manifest sólo contiene
versiones, contadores, estados y códigos de error, nunca rutas, originales, sintéticos o mappings.

