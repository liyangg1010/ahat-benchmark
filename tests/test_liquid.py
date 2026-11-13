import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from helpers import PROJECT, DOMAIN, VAL, FakeClient, scene, PLAN
from ahat_benchmark.domains import resolve_domain, domain_binding, BASE_DOMAIN, LIQUID_DOMAIN
from ahat_benchmark.pddl import full_problem, final_state, simulate, sexpr
from ahat_benchmark.val.validator import validate_plan
from ahat_benchmark.vendor.scene_graph import SceneGraphManager
from ahat_benchmark.judge.evaluator import RubricEvaluator
from ahat_benchmark.judge.prompts import PROMPTS, LIQUID_PROMPTS
from ahat_benchmark.pipeline.val_stage import run_val_stage
from ahat_benchmark.pipeline.judge_stage import run_judge_stage
from ahat_benchmark.pipeline.summarize import summarize

LIQUID=resolve_domain(LIQUID_DOMAIN)


def small_scene():
    return {'rooms':[{'name':'room_1','states':{}}],
        'furnitures':[{'name':'table_1','states':{}},{'name':'sink_1','states':{'has_faucet':True}},
                      {'name':'stove_1','states':{'is_cooking_surface':True,'is_powered_on':True}}],
        'objects':[
            {'name':'kettle_1','states':{'is_liquid_container':True,'is_kettle':True,'is_filled':True,'contains_water':True,'contents_heated':True,'is_heating_container':True}},
            {'name':'cup_1','states':{'is_liquid_container':True}},
            {'name':'book_1','states':{}},
            {'name':'tea_1','states':{'tea_supply':True,'ingredient_available':True}},
            {'name':'machine_1','states':{'is_liquid_container':True,'is_coffee_machine':True,'can_dispense':True,'is_powered_on':True,'coffee_loaded':True}},
        ],'agent':[{'name':'agent_0','location':'cup_1','holding':'kettle_1'}],
        'person':[],'links':[['room_1','table_1','in'],['room_1','sink_1','in'],['room_1','stove_1','in'],
                           ['table_1','cup_1','on'],['table_1','book_1','on'],['table_1','tea_1','on'],['table_1','machine_1','on']]}


def checked(g,plan):return validate_plan(scene_graph=g,plan=plan,domain_path=LIQUID,val_executable=VAL,timeout_seconds=10)


class LiquidTests(unittest.TestCase):
    def test_faucet_requires_open_lid_only_for_openable_containers(self):
        g=small_scene();g['agent'][0].update(location='sink_1',holding='cup_1')
        g['links']=[l for l in g['links'] if l[1]!='cup_1']
        fill=['(fill_from_faucet agent_0 cup_1 sink_1)']
        self.assertEqual(checked(g,fill)['status'],'valid')  # An ordinary cup has no lid.
        g['objects'][1]['states']['can_be_opened']=True
        self.assertEqual(checked(g,fill)['status'],'invalid')  # Omitted is_open means closed.
        g['objects'][1]['states']['is_open']=False
        self.assertEqual(checked(g,fill)['status'],'invalid')
        g['objects'][1]['states']['is_open']=True
        result=checked(g,fill)
        self.assertEqual(result['status'],'valid',result)
        state=final_state(result['problem_pddl'],fill,LIQUID)
        self.assertIn(['contains_water','cup_1'],state)
        self.assertIn(['is_open','cup_1'],state)
        self.assertNotIn(['contents_heated','cup_1'],state)

    def test_retained_bottles_need_opening_and_keep_their_original_outcomes(self):
        from test_next_to import native_goal
        import runpy
        migration=runpy.run_path(str(PROJECT/'scripts/repair_bottle_refill.py'))
        rows={r['id']:r for r in map(json.loads,(PROJECT/'benchmarks/ahat_eval_set.jsonl').read_text().splitlines())}
        self.assertFalse(migration['REMOVE'] & rows.keys())
        archived=json.loads((PROJECT/'benchmarks/bottle-refill-v1/pruned.json').read_text())
        self.assertEqual({r['original_record']['id'] for r in archived},migration['REMOVE'])
        for cid,bottle in migration['KEEP'].items():
            row=rows[cid]
            self.assertEqual(row['domain_id'],LIQUID_DOMAIN)
            self.assertEqual(migration['repair'](row),row)
            self.assertEqual(checked(row['scene_graph'],row['plan'])['status'],'valid')
            self.assertTrue(native_goal(row['scene_graph'],row['plan'],row['liquid_reference']['goals'],LIQUID))
            without_open=[s for s in row['plan'] if sexpr(s)[0]!='open']
            self.assertEqual(checked(row['scene_graph'],without_open)['status'],'invalid')
            pickup=next(i for i,s in enumerate(row['plan']) if sexpr(s)[0]=='pick_from_surface')
            self.assertEqual(row['plan'][pickup-1],f'(open agent_0 {bottle})')
            self.assertNotIn(f'(not (is_open {bottle}))',row['liquid_reference']['goals'])

    def test_generated_domain_preserves_all_common_actions_and_audited_base(self):
        from ahat_benchmark.vendor.scene_graph import PDDLDomainParser
        base=PDDLDomainParser(DOMAIN.read_text());liquid=PDDLDomainParser(LIQUID.read_text())
        liquid_only={'fill_from_faucet','fill_device_with_water','pour_into','pour','dispense_from_device'}
        self.assertFalse(liquid_only & base.actions.keys())
        self.assertTrue(liquid_only <= liquid.actions.keys())
        for name, action in base.actions.items():
            self.assertEqual(action,liquid.actions[name],name)
        self.assertEqual(hashlib.sha256(DOMAIN.read_bytes()).hexdigest(),
                         '0280dcd8e4469e5071e98214c2c5ab1dcc882c5d4cd9f192f3c6e0d1f5635fdd')

    def test_ordinary_domain_rejects_liquid_actions(self):
        graph=scene()
        for step in ('(fill_from_faucet agent_0 cup_1 table_1)',
                     '(fill_device_with_water agent_0 table_1)',
                     '(dispense_from_device agent_0 table_1 cup_1)',
                     '(pour_into agent_0 cup_1 lid_1)',
                     '(pour agent_0 cup_1 table_1)'):
            with self.subTest(step=step):
                result=validate_plan(scene_graph=graph,plan=[step],domain_path=DOMAIN,
                                     val_executable=VAL,timeout_seconds=10)
                self.assertEqual(result['status'],'invalid',result)
                self.assertEqual(result['invalid_action'],step)

    def test_transfer_and_refill_clear_only_content_heat(self):
        g=small_scene();g['objects'][0]['states']['heated']=True
        plan=['(pour_into agent_0 kettle_1 cup_1)','(navigate agent_0 cup_1 sink_1)','(fill_from_faucet agent_0 kettle_1 sink_1)']
        v=checked(g,plan);self.assertEqual(v['status'],'valid',v)
        state=final_state(v['problem_pddl'],plan,LIQUID)
        self.assertIn(['contents_heated','cup_1'],state)
        self.assertIn(['contains_water','cup_1'],state)
        self.assertIn(['contains_water','kettle_1'],state)
        self.assertNotIn(['contents_heated','kettle_1'],state)
        self.assertIn(['heated','kettle_1'],state)
        manager=SceneGraphManager(g,str(LIQUID))
        for i,p in enumerate(plan):
            a=sexpr(p);manager.apply_action(a[0],a[1:])
            self.assertEqual(final_state(full_problem(manager.scene_graph,LIQUID),[],LIQUID),final_state(v['problem_pddl'],plan[:i+1],LIQUID))

    def test_cold_water_does_not_become_hot_and_cannot_make_tea(self):
        g=small_scene();g['objects'][0]['states']['contents_heated']=False
        g['objects'][1]['states']['tea_loaded']=True
        plan=['(pour_into agent_0 kettle_1 cup_1)','(navigate agent_0 cup_1 table_1)','(place_on_surface agent_0 kettle_1 table_1)','(navigate agent_0 table_1 cup_1)','(brew_tea agent_0 cup_1)']
        self.assertEqual(checked(g,plan)['status'],'invalid')
        state=final_state(full_problem(g,LIQUID),plan[:1],LIQUID)
        self.assertNotIn(['contents_heated','cup_1'],state)
        self.assertNotIn(['contains_tea','cup_1'],state)

    def test_coffee_requires_water_and_raw_ingredient_cannot_be_reused(self):
        g=small_scene();g['agent'][0].update(location='machine_1',holding=None)
        g['links']=[l for l in g['links'] if l[1]!='cup_1']+[['machine_1','cup_1','on']]
        self.assertEqual(checked(g,['(dispense_from_device agent_0 machine_1 cup_1)'])['status'],'invalid')
        g=small_scene();g['agent'][0].update(holding='tea_1')
        g['links']=[l for l in g['links'] if l[1]!='tea_1']
        p=['(load_tea agent_0 tea_1 cup_1)','(navigate agent_0 cup_1 kettle_1)','(load_tea agent_0 tea_1 kettle_1)']
        self.assertEqual(checked(g,p)['status'],'invalid')

    def test_noncontainer_cannot_receive_and_conflicting_contents_fail(self):
        g=small_scene();g['agent'][0]['location']='book_1'
        self.assertEqual(checked(g,['(pour_into agent_0 kettle_1 book_1)'])['status'],'invalid')
        g['objects'][0]['states']['contains_tea']=True
        with self.assertRaisesRegex(ValueError,'exactly one'):
            full_problem(g,LIQUID)

    def test_stovetop_requires_vessel_on_actual_powered_stove(self):
        g=small_scene();g['objects'][0]['states']['contents_heated']=False
        g['agent'][0].update(holding=None,location='stove_1');g['links'].append(['stove_1','kettle_1','on'])
        plan=['(heat_liquid_on_stove agent_0 kettle_1 stove_1)']
        v=checked(g,plan);self.assertEqual(v['status'],'valid',v)
        self.assertIn(['contents_heated','kettle_1'],final_state(v['problem_pddl'],plan,LIQUID))
        g['links'][-1]=['table_1','kettle_1','on'];self.assertEqual(checked(g,plan)['status'],'invalid')

    def test_wrong_domain_rejects_liquid_facts_and_export_never_leaks_references(self):
        with self.assertRaisesRegex(ValueError, 'require the liquid domain'):
            full_problem(small_scene(), DOMAIN)
        from ahat_benchmark.inference_inputs import export_inputs
        with tempfile.TemporaryDirectory() as directory:
            output = export_inputs('ahat-medium', Path(directory) / 'inputs.json')
            self.assertEqual(set(output['domains']), {BASE_DOMAIN, LIQUID_DOMAIN})
            for row in output['cases']:
                self.assertNotIn('plan', row)
                self.assertNotIn('reference_goal', row)
                self.assertNotIn('liquid_reference', row)
                self.assertEqual(row['domain_sha256'], output['domains'][row['domain_id']]['sha256'])
                self.assertIn('(:goal (and))', row['problem_pddl'])

    def test_conditional_effects_read_prestate_and_forall_bindings(self):
        problem='(define (problem p) (:objects a b - thing) (:init (p a)))'
        actions={'test':{'parameters':{},'effect':['and',['not',['p','a']],['p','b'],['forall',['?x','-','thing'],['when',['p','?x'],['q','?x']]]]}}
        state=simulate(problem,['(test)'],actions,type_parents={'thing':'object'})
        self.assertIn(['q','a'],state);self.assertNotIn(['q','b'],state)

    def test_mixed_domain_pipeline_and_inference_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            d=Path(directory);g=small_scene()
            cases=[{'id':'ordinary','instruction':'Pick up the cup','scene_graph':scene(),'domain_id':BASE_DOMAIN},
                   {'id':'liquid','instruction':'Pour hot water into the cup','scene_graph':g,'domain_id':LIQUID_DOMAIN}]
            data=json.dumps(cases).encode();(d/'cases.json').write_bytes(data)
            (d/'manifest.json').write_text(json.dumps({'case_count':2,'data_sha256':hashlib.sha256(data).hexdigest()}))
            registry=d/'datasets.yaml';registry.write_text('datasets:\n  mixed: cases.json\n')
            infer=d/'inference.json';results=[{'id':'ordinary','plan':PLAN,**domain_binding(BASE_DOMAIN)},
                {'id':'liquid','plan':['(pour_into agent_0 kettle_1 cup_1)'],**domain_binding(LIQUID_DOMAIN)}]
            infer.write_text(json.dumps({'results':results}));vp=d/'val.json';jp=d/'judge.json'
            kw=dict(dataset='mixed',inference_path=infer,registry_path=registry)
            vals=run_val_stage(**kw,output_path=vp,domain_path=DOMAIN,val_executable=VAL,timeout_seconds=10,workers=2)
            self.assertEqual({r['status'] for r in vals['cases']},{'valid'})
            client=FakeClient();evaluator=RubricEvaluator(client=client,model='fake',domain_path=DOMAIN,max_attempts=1)
            result=run_judge_stage(**kw,val_results_path=vp,output_path=jp,evaluator=evaluator,workers=2)
            self.assertEqual({r['status'] for r in result['cases']},{'success'})
            sent=[r['messages'][0]['content'] for r in client.calls]
            for key in PROMPTS:self.assertIn(PROMPTS[key],sent);self.assertIn(LIQUID_PROMPTS[key],sent)
            summary=summarize(**kw,val_results_path=vp,judge_results_path=jp,output_path=d/'final.json',domain_path=DOMAIN)
            self.assertEqual(summary['statistics']['by_domain'][LIQUID_DOMAIN]['total_cases'],1)
            run_judge_stage(**kw,val_results_path=vp,output_path=jp,evaluator=evaluator,workers=2)
            self.assertEqual(len(client.calls),8)
            results[1]['domain_id']=BASE_DOMAIN;infer.write_text(json.dumps({'results':results}))
            with self.assertRaisesRegex(ValueError,'Inference domain mismatch'):
                run_val_stage(**kw,output_path=d/'bad.json',domain_path=DOMAIN,val_executable=VAL,timeout_seconds=10,workers=1)

if __name__=='__main__':unittest.main()
