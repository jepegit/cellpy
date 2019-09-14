import logging
import os

from cellpy import prms
from cellpy.utils.batch_tools.batch_helpers import generate_folder_names


def csv_dumper(**kwargs):
    """dump data to csv"""
    logging.info("dumping to csv")
    barn = kwargs["barn"]
    farms = kwargs["farms"]
    experiments = kwargs["experiments"]
    for experiment, farm in zip(experiments, farms):
        name = experiment.journal.name
        project = experiment.journal.project
        project_dir, batch_dir, raw_dir = experiment.journal.paginate()
        if batch_dir is None:
            logging.info("have to generate folder-name on the fly")
            out_data_dir, project_dir, batch_dir, raw_dir = generate_folder_names(
                name, project
            )

        if barn == "batch_dir":
            out_dir = batch_dir
        elif barn == "project_dir":
            out_dir = project_dir
        elif barn == "raw_dir":
            out_dir = raw_dir
        else:
            out_dir = barn

        for animal in farm:
            file_name = os.path.join(out_dir, "summary_%s_%s.csv" % (animal.name, name))
            logging.info(f"> {file_name}")
            animal.to_csv(file_name, sep=prms.Reader.sep)


def excel_dumper(**kwargs):
    """Dump data to excel xlxs-format."""
    pass


def origin_dumper(**kwargs):
    """Dump data to a format suitable for use in OriginLab."""
    pass


def ram_dumper(**kwargs):
    """Dump data to 'memory' for later usage."""
    logging.debug("trying to save stuff in memory")
    farms = kwargs["farms"]
    experiments = kwargs["experiments"]
    engine = kwargs["engine"]

    try:
        engine_name = engine.__name__
    except AttributeError:
        engine_name = engine.__dict__.__name__

    accepted_engines = ["summary_engine"]
    if engine_name in accepted_engines:
        logging.debug(
            "found the engine that I will try to dump from: " f"{engine_name}"
        )

        for experiment, farm in zip(experiments, farms):
            name = experiment.journal.name
            project = experiment.journal.project
            experiment.memory_dumped[engine_name] = farm
            logging.debug(f"farm put into memory_dumped ({project}::{name})")


def screen_dumper(**kwargs):
    """Dump data to screen."""
    farms = kwargs["farms"]
    engine = kwargs["engine"]
    logging.info("dumping to screen")

    print(f"\n[Screen dumper] ({engine})")
    try:
        if len(farms) == 1:
            print(f"You have one farm with little pandas.")

        else:
            print(f"You have {len(farms)} farms with little pandas.")
    except TypeError:
        print(" - your farm has burned to the ground.")
    else:
        for number, farm in enumerate(farms):
            print(f"[#{number+1}]You have {len(farm)} " f"little pandas in this farm.")
            for animal in farm:
                print(80 * "=")
                try:
                    print(animal.name)
                except AttributeError:
                    print("no-name")
                print(80 * "-")
                print(animal.head(5))
                print()
