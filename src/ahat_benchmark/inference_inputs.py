"""Reference-free inference export with fixed per-task domain fingerprints."""
from pathlib import Path
from .datasets import load_eval_set
from .domains import resolve_domain, domain_binding
from .pddl import full_problem
from .io import write_json_atomic


def export_inputs(dataset: str, output_path: Path, registry_path: Path | None = None) -> dict:
    cases=load_eval_set(dataset,registry_path=registry_path)
    domains={};records=[]
    for case in cases:
        binding=domain_binding(case.domain_id)
        domain=resolve_domain(case.domain_id)
        domains[binding['domain_id']]={'sha256':binding['domain_sha256'],'pddl':domain.read_text()}
        records.append({'id':case.id,'instruction':case.instruction,'scene_graph':case.scene_graph,
                        **binding,'problem_pddl':full_problem(case.scene_graph,domain)})
    result={'schema_version':'2.0','dataset':dataset,'domains':domains,'cases':records}
    write_json_atomic(output_path,result)
    return result
