"""Form-owned validation for subject slots.

These validators keep subject correction inside the active Rasa form. Business
actions still resolve defensively when invoked directly, but normal dialogue
paths submit only canonical subject names.
"""

from typing import Any, Dict, Text

import os
from dotenv import load_dotenv
from rasa_sdk import FormValidationAction, Tracker
from rasa_sdk.executor import CollectingDispatcher
from supabase import Client, create_client

from actions.subject_catalog import SubjectCatalogRepository
from actions.subject_resolver import SubjectResolver


load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
subject_catalog = SubjectCatalogRepository(lambda: supabase, ttl_seconds=600)
subject_resolver = SubjectResolver()


def _validate_subject(
    slot_value: Any,
    dispatcher: CollectingDispatcher,
) -> Dict[Text, Any]:
    if not slot_value:
        dispatcher.utter_message(
            "❌ No tengo la materia especificada. Por favor, indica qué materia necesitas."
        )
        return {"materia": None}

    try:
        catalog = subject_catalog.get_subjects()
        status, resolution = subject_resolver.resolve(catalog, str(slot_value))

        if status == "not_found":
            dispatcher.utter_message(
                f"😕 No se encontró la materia '{slot_value}' en la base de datos. "
                "Por favor, intenta ingresando otra materia."
            )
            return {"materia": None}

        if status == "ambiguous":
            options = ", ".join(
                sorted({subject["nombre"] for subject in resolution})
            )
            dispatcher.utter_message(
                f"❓ Encontré varias materias que coinciden con '{slot_value}': "
                f"{options}. Por favor, especifica cuál necesitas."
            )
            return {"materia": None}

        return {"materia": resolution["nombre"]}
    except Exception as error:
        print(f"Error al validar materia en formulario: {error}")
        dispatcher.utter_message(
            "❌ Hubo un error al consultar el catálogo de materias. "
            "Por favor, intenta nuevamente más tarde."
        )
        return {"materia": None}


class _SubjectFormValidatorMixin:
    def validate_materia(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        return _validate_subject(slot_value, dispatcher)


class ValidateAsistenciaForm(_SubjectFormValidatorMixin, FormValidationAction):
    def name(self) -> Text:
        return "validate_asistencia_form"


class ValidateNotasForm(_SubjectFormValidatorMixin, FormValidationAction):
    def name(self) -> Text:
        return "validate_notas_form"


class ValidateRequisitosForm(_SubjectFormValidatorMixin, FormValidationAction):
    def name(self) -> Text:
        return "validate_requisitos_form"


class ValidateConsultarMesasForm(_SubjectFormValidatorMixin, FormValidationAction):
    def name(self) -> Text:
        return "validate_consultar_mesas_form"


class ValidateFechasParcialesForm(_SubjectFormValidatorMixin, FormValidationAction):
    def name(self) -> Text:
        return "validate_fechas_parciales_form"


class ValidateCancelarMesaForm(_SubjectFormValidatorMixin, FormValidationAction):
    def name(self) -> Text:
        return "validate_cancelar_mesa_form"
