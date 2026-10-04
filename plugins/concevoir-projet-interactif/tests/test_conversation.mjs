import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const code = readFileSync(new URL('../skills/concevoir-projet-interactif/assets/questionnaire-conversation.js', import.meta.url), 'utf8');
const context = vm.createContext({});
vm.runInContext(code, context);
const choice = (id, needs_clarification = false) => ({id, label:id.toUpperCase(), needs_clarification});
const data = {project:{title:'Projet de test',slug:'test-project'},round_id:'T01',storage_key:'test-T01',locale:'fr',
  sections:[{title:'Orientation',questions:[
    {id:'open',title:'Résultat',type:'open',allow_note:true},
    {id:'decision',title:'Public ?',type:'decision',choices:[choice('yes'),choice('maybe',true)]},
    {id:'single',title:'Premier public',type:'single_choice',choices:[choice('a'),choice('b')]},
    {id:'multi',title:'Supports',type:'multi_choice',choices:[choice('web'),choice('mobile')]},
    {id:'scale',title:'Priorité',type:'scale',scale:{min:0,max:10,step:2,default:4}},
    {id:'ranking',title:'Classement',type:'ranking',choices:[choice('a'),choice('b')]}
  ]}]};
const make = () => context.createQuestionnaireSession(JSON.parse(JSON.stringify(data)));
const plain = value => JSON.parse(JSON.stringify(value));

test('no default scale, ranking or decision is accepted', () => {
  const session=make();
  assert.equal(session.completion().unanswered.length,6);
  assert.deepEqual(plain(session.payload().answers),{});
});
test('all six types and raw notes survive sending with project and round identity', async () => {
  const session=make();
  const raw='  réponse avec `code`, accents et\nune deuxième ligne  ';
  session.setAnswer('open',raw);session.setNote('open','Oui, mais seulement avec cette nuance.');
  session.setAnswer('decision','maybe');session.setNote('decision','Je veux préciser le public.');
  session.setAnswer('single','a');session.setAnswer('multi',['web','mobile']);session.setAnswer('scale',0);session.setAnswer('ranking',['b','a']);
  assert.deepEqual(plain(session.completion()),{unanswered:[],clarification:[]});
  let message;
  assert.equal((await session.send({sendFollowUpMessage:async m=>{message=m;return true;}})).status,'submitted');
  const payload=JSON.parse(message.prompt.split('\n```json\n')[1].split('\n```')[0]);
  assert.equal(payload.answers.open,raw);assert.equal(payload.notes.open,'Oui, mais seulement avec cette nuance.');
  assert.deepEqual(payload.answers.ranking,['b','a']);assert.equal(payload.project.slug,'test-project');
  assert.equal(payload.round_id,'T01');assert.equal(payload.storage_key,'test-T01');assert.equal(payload.schema,'project-workshop-answers-v2');
});
test('whitespace remains raw but does not count as a completed answer', () => {
  const session=make();session.setAnswer('open','   ');
  assert.equal(session.payload().answers.open,'   ');assert.equal(session.completion().unanswered.length,6);
});
test('maybe without a note remains a clarification, not a yes', () => {
  const session=make();session.setAnswer('decision','maybe');
  assert.deepEqual(plain(session.completion().clarification),['decision']);
  assert.equal(session.payload().answers.decision,'maybe');
});
test('invalid choices, duplicate rankings and misaligned scales are rejected', () => {
  for(const [id,value] of [['single','unknown'],['multi',['web','web']],['scale',3],['scale',NaN],['ranking',['a','a']]]) {
    assert.throws(()=>make().setAnswer(id,value));
  }
});
test('cross-project, cross-round and invalid restores preserve the original answers', () => {
  const session=make();session.setAnswer('open','original');const baseline=plain(session.payload());
  const mutations=[p=>p.project.slug='elsewhere',p=>p.round_id='T02',p=>p.storage_key='other',
    p=>p.answers.single='invalid',p=>p.notes.scale='not allowed',p=>p.answers=JSON.parse('{"__proto__":"bad"}')];
  for(const change of mutations){const p=plain(baseline);change(p);assert.throws(()=>session.restore(p));assert.deepEqual(plain(session.payload()),baseline);}
  const restored=make();restored.restore(baseline);assert.deepEqual(plain(restored.payload()),baseline);
});
test('a missing bridge never reports success and never mutates answers', async () => {
  const session=make();session.setAnswer('open','kept');
  assert.equal((await session.send(undefined)).status,'unavailable');assert.equal(session.payload().answers.open,'kept');
});
test('double click while pending and identical repeat are suppressed; edits can be sent', async () => {
  const session=make();let finish,calls=0;
  const bridge={sendFollowUpMessage:()=>{calls++;return new Promise(resolve=>{finish=resolve;});}};
  const first=session.send(bridge);assert.equal((await session.send(bridge)).status,'pending');assert.equal(calls,1);
  finish(true);await first;assert.equal((await session.send(bridge)).status,'already-sent');assert.equal(calls,1);
  session.setAnswer('open','new');const second=session.send(bridge);assert.equal(calls,2);finish();await second;
});
test('cancellation and rejected sends preserve answers and allow retry', async () => {
  const session=make();session.setAnswer('open','kept');
  for(const result of [false,{cancelled:true},{status:'canceled'}])assert.equal((await session.send({sendFollowUpMessage:async()=>result})).status,'cancelled');
  await assert.rejects(session.send({sendFollowUpMessage:async()=>{throw Error('cancelled by host');}}));
  await assert.rejects(session.send({sendFollowUpMessage:async()=>({success:false})}));
  assert.equal(session.payload().answers.open,'kept');
  assert.equal((await session.send({sendFollowUpMessage:async()=>true})).status,'submitted');
});
test('editing while a snapshot is pending does not mark the new answers as sent', async () => {
  const session=make();session.setAnswer('open','first');let finish;
  const sending=session.send({sendFollowUpMessage:()=>new Promise(resolve=>{finish=resolve;})});
  session.setAnswer('open','second');finish();await sending;
  let prompt;await session.send({sendFollowUpMessage:async message=>{prompt=message.prompt;}});
  assert.match(prompt,/second/);
});
test('long answers are never silently truncated or sent', async () => {
  const session=make();session.setAnswer('open','a'.repeat(60000));let calls=0;
  await assert.rejects(session.send({sendFollowUpMessage:async()=>{calls++;}}));
  assert.equal(calls,0);assert.equal(session.payload().answers.open.length,60000);
});
test('void acknowledgement is ambiguous: no fake success, retry remains possible after checking', async () => {
  const session=make();let calls=0;const bridge={sendFollowUpMessage:async()=>{calls++;}};
  assert.equal((await session.send(bridge)).status,'requested');
  assert.equal((await session.send(bridge)).status,'check-before-retry');assert.equal(calls,1);
  assert.equal((await session.send(bridge,{retry:true})).status,'requested');assert.equal(calls,2);
});
