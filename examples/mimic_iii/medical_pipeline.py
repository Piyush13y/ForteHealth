import sys
import yaml
from termcolor import colored

from forte.common.configuration import Config
from forte.data.data_pack import DataPack
from forte.data.readers import PlainTextReader
from forte.pipeline import Pipeline
from forte.processors.writers import PackIdJsonPackWriter
from ftx.medical.clinical_ontology import NegationContext, MedicalEntityMention

from ft.onto.base_ontology import (
    Token,
    Sentence,
    EntityMention,
)
from fortex.spacy import SpacyProcessor

from fortex.health.readers.mimic3_note_reader import Mimic3DischargeNoteReader
from fortex.health.processors.negation_context_analyzer import (
    NegationContextAnalyzer,
)


def main(
    input_path: str,
    output_path: str,
    max_packs: int = -1,
    use_mimic3_reader: bool = True,
):
    pl = Pipeline[DataPack]()

    if use_mimic3_reader is False:
        pl.set_reader(PlainTextReader())
    else:
        pl.set_reader(
            Mimic3DischargeNoteReader(), config={"max_num_notes": max_packs}
        )

    config = Config(yaml.safe_load(open("config.yml", "r")), None)
    pl.add(SpacyProcessor(), config.Spacy)
    pl.add(NegationContextAnalyzer(), config.Negation)

    pl.add(
        PackIdJsonPackWriter(),
        {
            "output_dir": output_path,
            "indent": 2,
            "overwrite": True,
            "drop_record": True,
            "zip_pack": True,
        },
    )

    pl.initialize()

    packs = pl.process_dataset(input_path)
    for pack in packs:
        show_data(pack)


def show_data(pack: DataPack):
    for sentence in pack.get(Sentence):
        sent_text = sentence.text
        print(colored("Sentence:", "red"), sent_text, "\n")

        tokens = [
            (token.text, token.pos) for token in pack.get(Token, sentence)
        ]
        entities = [
            (entity.text, entity.ner_type)
            for entity in pack.get(EntityMention, sentence)
        ]

        medical_entities = []
        for entity in pack.get(MedicalEntityMention, sentence):
            for ent in entity.umls_entities:
                medical_entities.append(ent)

        negation_contexts = [
            (negation_context.text, negation_context.polarity)
            for negation_context in pack.get(NegationContext, sentence)
        ]

        print(colored("Tokens:", "red"), tokens, "\n")
        print(colored("Entity Mentions:", "red"), entities, "\n")
        print(
            colored("UMLS Entity Mentions detected:", "cyan"),
            medical_entities,
            "\n",
        )
        print(
            colored("Entity Negation Contexts:", "cyan"),
            negation_contexts,
            "\n",
        )

        input(colored("Press ENTER to continue...\n", "green"))


main(sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4].lower() == "true")
