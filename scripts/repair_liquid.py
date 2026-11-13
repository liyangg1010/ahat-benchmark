#!/usr/bin/env python3
"""Reviewed liquid-v1 migration. Dry-run by default; originals archived on write.

Explicit task specifications are independent of model output. The migration
never infers domain assignment from a submitted plan. New reference assertions
are witnesses consisting of both action coverage and final outcomes, not a
claim that final state alone proves every historical instruction constraint.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from ahat_benchmark.domains import LIQUID_DOMAIN, BASE_DOMAIN, resolve_domain
from ahat_benchmark.scene import normalize_links
from ahat_benchmark.pddl import sexpr
from ahat_benchmark.vendor.scene_graph import SceneGraphManager
from ahat_benchmark.val.validator import validate_plan

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'benchmarks/ahat_eval_set.jsonl'
DOMAIN=ROOT/'vendor/pddl/domain_liquid_v1.pddl'
REVISION='liquid-v1'
QUARANTINE={
 'c4eaedfe': 'Instruction requires a stove; scene has no stove/cooking surface. Old plan used a powered kettle on an island.',
 '83e9c29c': 'Kitchen boiling preparation has no kitchen water source in the scene; old reference filled from a bathroom bathtub. Restore after a documented scene repair.',
 'e78432e1': 'Vegetable patch is absent; old reference poured into the outdoor room itself. A room cannot stand for an unspecified planting target.',
 'acba2bf0': 'Hot bath requires a declared hot-water source or bath-heating capability; neither is provided.',
 'e2589b66': 'Warm shower preparation lacks a declared warm-water supply and a clear shower-ready outcome; a filled wash basin is insufficient.',
 '9c120c15': 'Night-time warmth/retention is outside the no-time/no-cooling model; old plan also lacks a hot-water pour.',
 'f740c053': 'Gourmet quality has no operational criterion; ordinary coffee production cannot certify it.',
}
# Only capability evidence on an explicitly named existing sink cabinet is added.
FAUCET_FIX={'44a3890d':'sink_cabinet_46','bd6d5204':'sink_cabinet_38','12b30bd2':'sink_cabinet_60'}
# Water-only references: container, source, destination (person or surface; None = keep held).
WATER={
 '6e590abe':('reusable_water_bottle_24','sink_67','person_0'),
 'c172ca4c':('kettle_61','shower_stall_120','person_0'),
 '6f3adc5c':('drinking_glass_63','bathtub_33','person_0'),
 '44a3890d':('reusable_water_bottle_47','sink_cabinet_46','desk_9'),
 '679dc145':('watering_can_18','sink_60','person_0'),
 'baebc10b':('reusable_water_bottle_25','sink_66','bed_55'),
 '41eef001':('vase_0','cabinet_21','stool_15'),
 'ca93f23c':('reusable_water_bottle_70','shower_stall_55','kitchen_island_122'),
}
# Kettle, water source, working surface, receiving cup, final destination, optional tea supply.
DRINK={
 'd3512291':('electric_kettle_23','sink_3','sink_3','mug_24','person_0',None),
 'bd6d5204':('electric_kettle_32','sink_cabinet_38','kitchen_island_58','mug_33','table_57',None),
 '99c7a3e4':('electric_kettle_40','sink_63','dining_table_53','ceramic_mug_41','person_0','box_of_tea_bags_42'),
 'a6858c23':('electric_kettle_17','sink_4','dining_table_35','teacup_18','person_0','tea_box_19'),
 '3a12822b':('electric_kettle_44','sink_6','dining_table_90','teacup_45','person_0','tea_container_46'),
 '6d1fc47f':('electric_kettle_14','sink_3','dining_table_50','ceramic_cup_17','person_0',None),
 'c77c47ae':('electric_kettle_35','sink_74','dining_table_59','teacup_36','bed_56',None),
}
COFFEE={
 'f8e914bb':('coffee_machine_16','mug_17','coffee_pod_18','bathtub_26','person_0'),
 '2cd06e0a':('coffee_machine_39','coffee_mug_40','coffee_pod_box_41','bathtub_79','kitchen_island_84'),
 '12b30bd2':('coffee_machine_36','ceramic_mug_37','coffee_canister_38','sink_cabinet_60','person_0'),
 '05f9fb16':('espresso_maker_86','coffee_mug_43','coffee_pod_box_44','sink_95','nightstand_54'),
}
PLANTS={
 '8b696fe2':('watering_can_22','sink_55',['potted_plant_34']),
 '8a288187':('watering_can_24','sink_67',['potted_plant_40','potted_plant_41']),
 '4377c209':('watering_can_32','bathtub_117',['potted_herbs_33']),
}
NOODLES={
 '23178c37':('electric_kettle_44','sink_6','sink_6','instant_noodle_cup_45','dining_table_90','spoon_46'),
 '72d3763d':('electric_kettle_45','shower_stall_75','kitchen_island_117','instant_noodle_cup_46','dining_table_82',None),
}

def sha(data):return hashlib.sha256(data).hexdigest()
def nodes(scene):return {n['name']:n for v in scene.values() if isinstance(v,list) for n in v if isinstance(n,dict) and 'name'in n}
def mark(scene,name,**flags):nodes(scene)[name].setdefault('states',{}).update(flags)
def container(scene,name,kind=None,hot=False):
    mark(scene,name,is_liquid_container=True,is_filled=kind is not None,contents_heated=hot,
         **{'contains_'+k:k==kind for k in ('water','tea','coffee','other_drink')})

class Plan:
    def __init__(self, scene, domain=DOMAIN):
        self.manager=SceneGraphManager(scene,str(domain));self.steps=[];self.goals=[]
        self.ag=scene['agent'][0]['name']
    @property
    def scene(self):return self.manager.scene_graph
    def at(self,name):
        old=self.scene['agent'][0]['location']
        if old!=name:self.do('navigate',old,name)
    def do(self,name,*args):
        self.manager.apply_action(name,[self.ag,*args]);self.steps.append('('+' '.join([name,self.ag,*args])+')')
    def support(self,obj):
        matches=[l for l in self.scene['links'] if l.get('from')==obj and l['relation'] in ('on','in')]
        if len(matches)!=1:raise ValueError(f'Ambiguous support for {obj}: {matches}')
        return matches[0]['relation'],matches[0]['to']
    def pick(self,obj):
        rel,s=self.support(obj)
        if rel=='in':
            self.open(s)
        self.at(obj);self.do('pick_from_surface' if rel=='on' else 'pick_from_receptacle',obj,s)
    def open(self,obj):
        st=nodes(self.scene)[obj].get('states',{})
        if st.get('can_be_opened') and not st.get('is_open'):
            self.at(obj);self.do('open',obj)
    def put(self,obj,dest):self.at(dest);self.do('place_on_surface',obj,dest)
    def move(self,obj,dest):self.pick(obj);self.put(obj,dest)
    def fill(self,obj,source):self.pick(obj);self.at(source);self.do('fill_from_faucet',obj,source)
    def power(self,obj):
        self.at(obj)
        if not nodes(self.scene)[obj].get('states',{}).get('is_powered_on'):self.do('power_on',obj)
    def heat(self,k,source,surface):
        self.fill(k,source);self.put(k,surface);self.power(k);self.do('heat_liquid_in_kettle',k)
    def pour(self,k,c,surface):
        self.pick(k);self.at(c);self.do('pour_into',k,c);self.put(k,surface)
    def load(self,kind,s,c,putback):
        self.open(s);self.pick(s);self.at(c);self.do('load_'+kind,s,c);self.put(s,putback)
    def deliver(self,obj,dest):
        self.pick(obj);self.finish_held(obj,dest)
    def finish_held(self,obj,dest):
        if dest.startswith('person_'):
            self.at(dest);self.do('hand_over_to_person',dest,obj);self.goals.append(f'(p_holding {dest} {obj})')
        else:
            self.put(obj,dest);self.goals.append(f'(item_on_surface {obj} {dest})')
    def content_goal(self,c,kind='water',hot=False):
        self.goals += [f'(is_filled {c})',f'(contains_{kind} {c})']
        if hot:self.goals.append(f'(contents_heated {c})')

def repair(row):
    r=copy.deepcopy(row);g=r['scene_graph'];key=r['id'][:8];note=[]
    if key in QUARANTINE:return None,QUARANTINE[key]
    if key in FAUCET_FIX:
        mark(g,FAUCET_FIX[key],has_faucet=True);note.append('Declare faucet capability on the existing instruction-named sink cabinet.')
    # Equipment-only instructions: preserve their intent without unnecessary liquid processing.
    if key in ('a9f01a35','8eaf1794'):
        p=Plan(g,resolve_domain(BASE_DOMAIN))
        if key=='a9f01a35':
            p.move('teapot_17','cabinet_27')
            p.goals=['(item_on_surface teapot_17 cabinet_27)','(item_on_surface electric_kettle_1 cabinet_27)']
        else:
            p.move('cup_30','counter_19');p.power('electric_kettle_1')
            p.goals=['(item_on_surface cup_30 counter_19)','(is_powered_on electric_kettle_1)']
        r['plan']=p.steps
        r['liquid_reference']={'goals':p.goals,'scope':'equipment_only','required_actions':p.steps}
        return r,'Equipment preparation only; no automatic tea/hot-water completion requirement.'
    migrated = key in WATER or key in DRINK or key in COFFEE or key in PLANTS or key in NOODLES or key in {'3b49cc0c','cea31743','184f5333','8708a9fe','1cdf223d','ed9e36b8','3a5724ed','7f0a1344'}
    if not migrated:return r,'Ready-drink transport; existing object identity and spatial semantics suffice.'
    r['domain_id']=LIQUID_DOMAIN
    # Explicit annotations of all task roles before constructing the initial state.
    if key in WATER:container(g,WATER[key][0])
    if key in DRINK:
        k,src,surf,c,dest,tea=DRINK[key];container(g,k);container(g,c);mark(g,k,is_kettle=True)
        if tea:mark(g,tea,tea_supply=True,ingredient_available=True)
    if key in COFFEE:
        machine,c,s,src,dest=COFFEE[key];container(g,machine);container(g,c)
        mark(g,machine,is_coffee_machine=True,can_dispense=True,is_powerable=True);mark(g,s,coffee_supply=True,ingredient_available=True)
    if key in PLANTS:
        c,src,plants=PLANTS[key];container(g,c)
        for target in plants:mark(g,target,is_plant_receiver=True,watered=False)
    if key in NOODLES:
        k,src,surf,c,dest,spoon=NOODLES[key];container(g,k);container(g,c);mark(g,k,is_kettle=True);mark(g,c,contains_noodles=True,noodles_prepared=False)
    if key=='3b49cc0c':container(g,'bathtub_9')
    if key=='cea31743':container(g,'kettle_28');mark(g,'kettle_28',is_kettle=True)
    if key=='184f5333':container(g,'hot_pot_saucepan_26')
    if key=='8708a9fe':
        container(g,'kettle_1');container(g,'bowl_2');mark(g,'kettle_1',is_kettle=True)
    if key=='1cdf223d':
        container(g,'cup_1','tea',True);note.append('Instruction explicitly fetches ready hot tea: declare initial tea/heated contents instead of fabricating a brewing requirement.')
    if key=='ed9e36b8':container(g,'drinking_cup_85');mark(g,'drinking_cup_85',requires_water_to_clean=True)
    if key=='3a5724ed':container(g,'water_glass_16')
    if key=='7f0a1344':
        container(g,'jug_1','water');note.append('Instruction identifies a pitcher of water: declare its initial water contents and explicitly inspect it after setting the table.')
    p=Plan(g)
    if key in WATER:
        c,src,dest=WATER[key];p.fill(c,src);p.finish_held(c,dest);p.content_goal(c)
    elif key in DRINK:
        k,src,surf,c,dest,tea=DRINK[key]
        if key=='bd6d5204':p.move(k,surf)
        # Retrieve enclosed cups before pouring; preserve the specified receiving location.
        rel,old=p.support(c)
        if rel=='in':p.move(c,surf)
        p.heat(k,src,surf);p.pour(k,c,surf)
        if tea:
            _,support=p.support(tea);p.load('tea',tea,c,support);p.at(c);p.do('brew_tea',c)
        p.deliver(c,dest);p.content_goal(c,'tea' if tea else 'water',True)
    elif key in COFFEE:
        machine,c,s,src,dest=COFFEE[key]
        # Fill the machine by pouring from the same mug used later to receive coffee.
        # This avoids treating a fixed espresso maker as a portable water vessel.
        p.fill(c,src);p.at(machine);p.do('pour_into',c,machine);p.put(c,machine)
        _,support=p.support(s);p.load('coffee',s,machine,support);p.power(machine)
        p.do('dispense_from_device',machine,c);p.deliver(c,dest);p.content_goal(c,'coffee',True)
    elif key in PLANTS:
        c,src,plants=PLANTS[key];p.pick(c)
        for target in plants:
            p.at(src);p.do('fill_from_faucet',c,src);p.at(target);p.do('water_plant',c,target);p.goals.append(f'(watered {target})')
    elif key in NOODLES:
        k,src,surf,c,dest,spoon=NOODLES[key]
        p.move(c,dest);p.heat(k,src,surf);p.pour(k,c,surf);p.at(c);p.do('prepare_instant_noodles',c)
        p.goals += [f'(item_on_surface {c} {dest})',f'(noodles_prepared {c})'];p.content_goal(c,hot=True)
        if spoon:p.move(spoon,dest);p.goals.append(f'(item_on_surface {spoon} {dest})')
    elif key=='3b49cc0c':
        p.at('bathtub_9');p.do('fill_device_with_water','bathtub_9');p.content_goal('bathtub_9')
    elif key=='cea31743':
        p.fill('kettle_28','pedestal_sink_13');p.put('kettle_28','kitchen_island_22');p.power('kettle_28')
        p.content_goal('kettle_28');p.goals.append('(is_powered_on kettle_28)')
        note.append('Instruction specifies filling and switching on to heat; do not require completed heating as an extra goal.')
    elif key=='184f5333':
        p.open('kitchen_cabinet_58');p.move('portable_induction_stove_25','kitchen_island_56')
        p.move('hot_pot_saucepan_26','kitchen_island_56');p.fill('hot_pot_saucepan_26','shower_stall_42');p.put('hot_pot_saucepan_26','kitchen_island_56');p.power('portable_induction_stove_25')
        p.content_goal('hot_pot_saucepan_26');p.goals += ['(item_on_surface portable_induction_stove_25 kitchen_island_56)','(item_on_surface hot_pot_saucepan_26 kitchen_island_56)','(is_powered_on portable_induction_stove_25)']
        note.append('Equipment preparation only: no request to put the saucepan on the stove or finish heating.')
    elif key=='8708a9fe':
        p.move('bowl_2','counter_bathroom_invented_1');p.heat('kettle_1','cabinet_112','counter_66');p.pour('kettle_1','bowl_2','counter_66')
        p.pick('cup_3');p.at('cabinet_112');p.do('clean_item_with_faucet','cup_3','cabinet_112');p.put('cup_3','counter_bathroom_invented_1')
        p.content_goal('bowl_2',hot=True);p.goals += ['(item_on_surface bowl_2 counter_bathroom_invented_1)','(item_on_surface cup_3 counter_bathroom_invented_1)','(is_clean cup_3)']
    elif key=='1cdf223d':
        for obj in ('laptop_1','notebook_1','cup_1','watch_1'):
            p.move(obj,'table_84');p.goals.append(f'(item_on_surface {obj} table_84)')
        p.content_goal('cup_1','tea',True)
    elif key=='ed9e36b8':
        p.pick('drinking_cup_85');p.at('sink_2');p.do('clean_item_with_faucet','drinking_cup_85','sink_2');p.do('fill_from_faucet','drinking_cup_85','sink_2');p.put('drinking_cup_85','dining_table_21')
        p.content_goal('drinking_cup_85');p.goals += ['(is_clean drinking_cup_85)','(item_on_surface drinking_cup_85 dining_table_21)']
        note.append('Minimal refreshment witness: clean drinking water served on the table; remove unrelated bath products. Subjective calming quality is not certified.')
    elif key=='3a5724ed':
        # Keep non-liquid service and arrangement choices; only enrich the water result.
        for step in row['plan']:
            a=sexpr(step);p.manager.apply_action(a[0],a[1:]);p.steps.append(step)
        p.content_goal('water_glass_16');p.goals += ['(item_on_surface water_glass_16 dining_table_17)','(item_on_surface fruit_bowl_86 dining_table_17)']
        note.append('Final assertions cover the drink/service; do not certify the contents of an unannotated fruit bowl.')
    elif key=='7f0a1344':
        for step in row['plan']:
            a=sexpr(step);p.manager.apply_action(a[0],a[1:]);p.steps.append(step)
        p.at('jug_1');p.do('inspect_water_container','jug_1');p.content_goal('jug_1')
        p.goals += ['(water_checked jug_1)'] + [f'(item_on_surface {n} table_30)' for n in ('plate_5','plate_6','spoon_5','spoon_6','casserole_18','jug_1')]
    r['plan']=p.steps
    r['liquid_reference']={'goals':p.goals,'scope':'plan_and_state_witness_not_necessary_goal',
        'required_actions':[s for s in p.steps if sexpr(s)[0] in {'fill_from_faucet','fill_device_with_water','load_tea','load_coffee','brew_tea','dispense_from_device','heat_liquid_in_kettle','heat_liquid_on_stove','pour_into','water_plant','prepare_instant_noodles','clean_item_with_faucet','inspect_water_container'}],
        'notes':note}
    return r,' '.join(note) or 'Explicit container contents, legal processing and instruction-matched reference.'


def migrate(rows):
    inventory=json.loads((ROOT/'docs/validation/liquid_instruction_current.json').read_text())
    candidates={x['id'] for x in inventory['records']}
    candidates.add('7f0a1344-6ce2-4860-8b0d-1d6de7219fdd')
    actions={'fill_from_faucet','fill_device_with_water','pour_into','pour','dispense_from_device'}
    candidates|={r['id'] for r in rows if any(sexpr(s)[0] in actions for s in r['plan'])}
    after=[];review=[];quarantine=[];originals=[]
    for source_index,r in enumerate(rows):
        if r['id'] not in candidates:after.append(r);continue
        new,reason=repair(r)
        decision='quarantine' if new is None else 'migrate' if new.get('domain_id')==LIQUID_DOMAIN else 'repair_equipment' if new!=r else 'retain_base'
        review.append({'source_index':source_index,'id':r['id'],'instruction':r['instruction'],'split':r['type'],'decision':decision,'reason':reason,'before_sha256':sha(json.dumps(r,sort_keys=True).encode())})
        if new is None:quarantine.append({'reason':reason,'original_record':r})
        else:after.append(new)
        if new!=r:originals.append(r)
    return after,review,quarantine,originals


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');parser.add_argument('--baseline',type=Path,help='rebuild this unpublished migration from its exact fingerprinted baseline');args=parser.parse_args()
    sync_path=ROOT/'benchmarks/hf_sync.json';sync=json.loads(sync_path.read_text())
    if 'local_liquid_v1' in sync and args.baseline is None:
        if sha(SOURCE.read_bytes()) != sync['local_liquid_v1']['result_data_sha256']:
            raise ValueError('Applied liquid migration source fingerprint changed; audit before rerunning')
        print('liquid-v1 already applied; source fingerprint verified');return
    before=(args.baseline or SOURCE).read_bytes()
    if args.baseline is not None and sha(before) != sync.get('local_liquid_v1',{}).get('base_data_sha256'):
        raise ValueError('Rebuild baseline does not match recorded migration origin')
    rows=[json.loads(l) for l in before.splitlines()]
    after,review,quarantine,originals=migrate(rows)
    failures=[]
    for r in after:
        if r['id'] not in {x['id'] for x in originals}:continue
        v=validate_plan(scene_graph=r['scene_graph'],plan=r['plan'],domain_path=resolve_domain(r.get('domain_id')),val_executable=ROOT/'vendor/val/Validate',timeout_seconds=10)
        if v['status']!='valid':failures.append({'id':r['id'],'result':v})
    report={'revision':REVISION,'base_sha256':sha(before),'active_count':len(after),'decisions':dict(Counter(x['decision'] for x in review)),'records':review}
    out=ROOT/'outputs/liquid-v1';out.mkdir(exist_ok=True,parents=True)
    (out/'candidate_review.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'candidate_failures.json').write_text(json.dumps(failures,indent=2)+'\n')
    (out/'candidate_after.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in after))
    print(json.dumps({'counts':report['decisions'],'active_count':len(after),'failures':len(failures)}))
    if failures:raise SystemExit('Reference validation failed; inspect outputs/liquid-v1/candidate_failures.json')
    if not args.write:return
    # Only write after validating every changed reference. Unmodified source lines are retained.
    raw={r['id']:line for r,line in zip(rows,before.splitlines(keepends=True))};old={r['id']:r for r in rows}
    SOURCE.write_bytes(b''.join(raw[r['id']] if r==old[r['id']] else (json.dumps(r,ensure_ascii=False)+'\n').encode() for r in after))
    archive=ROOT/'benchmarks/liquid-v1';archive.mkdir(exist_ok=True)
    (archive/'originals.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in originals))
    (archive/'quarantined.json').write_text(json.dumps(quarantine,ensure_ascii=False,indent=2)+'\n')
    report['result_sha256']=sha(SOURCE.read_bytes())
    (ROOT/'docs/validation/liquid_v1_inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    counts=dict(Counter(r['type'] for r in after));manifest=json.loads((ROOT/'benchmark_manifest.json').read_text())
    for split in ('easy','medium','open'):
        folder=ROOT/f'benchmarks/ahat-{split}';file=folder/'cases.json'
        projected=[{k:r[k] for k in ('id','instruction','scene_graph','domain_id') if k in r} for r in after if r['type']==split]
        file.write_text(json.dumps(projected,ensure_ascii=False,indent=2)+'\n')
        m=json.loads((folder/'manifest.json').read_text());parts=m['version'].split('.');parts[1]=str(int(parts[1])+1);parts[2]='0'
        m.update(version={'easy':'1.8.0','medium':'1.7.0','open':'1.8.0'}[split],schema_version='2.0',case_count=counts[split],data_sha256=sha(file.read_bytes()),domains=manifest['domains'],local_liquid_v1=REVISION)
        (folder/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    sync.update(case_count=len(after),split_counts=counts)
    sync['local_liquid_v1']={'version':REVISION,'base_data_sha256':sha(before),'result_data_sha256':sha(SOURCE.read_bytes()),'inventory_path':'docs/validation/liquid_v1_inventory.json','quarantined_ids':[x['original_record']['id'] for x in quarantine],'domain_counts':dict(Counter(r.get('domain_id',BASE_DOMAIN) for r in after)),'script_sha256':sha(Path(__file__).read_bytes())}
    for a in sync['artifacts']:
        path=ROOT/'benchmarks'/a['path'];a['sha256']=sha(path.read_bytes())
    sync_path.write_text(json.dumps(sync,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
