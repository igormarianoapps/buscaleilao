import test from 'node:test';
import assert from 'node:assert/strict';
import {groupAuctions,filterAuctions,feedFreshness,sourceLabel,emptyResultsMessage} from '../app/agenda.mjs';

const make = (id,state,overrides={}) => ({
  id, state, title:'Leilão', auction_date:'2099-11-03',
  auction_time:'10:00', organizer:'VIP Leilões', source_type:'private',
  status:'scheduled', source_url:'https://www.vipleiloes.com.br/agenda',
  ...overrides
});

test('VIP multi-state event is one result with searchable states',()=>{
  const items=[
    make('vip-event-one-go','GO',{event_id:'vip-event-one'}),
    make('vip-event-one-sp','SP',{event_id:'vip-event-one'}),
    make('vip-event-one-mg','MG',{event_id:'vip-event-one'})
  ];
  assert.equal(groupAuctions(items).length,1);
  assert.deepEqual(groupAuctions(items)[0].states,['GO','MG','SP']);
  assert.equal(filterAuctions(items,{state:'SP',today:'2099-11-01'}).length,1);
  assert.equal(filterAuctions(items,{state:'RJ',today:'2099-11-01'}).length,0);
});

test('different platforms and dates stay separate',()=>{
  const items=[
    make('vip-event-one-sp','SP',{event_id:'vip-event-one'}),
    make('vip-event-two-sp','SP',{event_id:'vip-event-two',auction_date:'2099-11-04'}),
    make('copart-2099-11-03-sp-osasco','SP',{organizer:'Copart'})
  ];
  assert.equal(groupAuctions(items).length,3);
});

test('date and status filters exclude expired and cancelled',()=>{
  const items=[
    make('vip-event-one-sp','SP',{event_id:'vip-event-one'}),
    make('old','GO',{auction_date:'2020-01-01'}),
    make('cancelled','SP',{status:'cancelled'})
  ];
  assert.equal(filterAuctions(items,{today:'2099-11-01',day:'2099-11-03'}).length,1);
  assert.equal(filterAuctions(items,{today:'2100-01-01'}).length,0);
});

test('similar VIP times without matching identity remain distinct',()=>{
 const items=[make('different-a','GO'),make('different-b','GO')];
 assert.equal(groupAuctions(items).length,2);
});

test('old collection is clearly marked stale',()=>{
 const now=Date.parse('2026-11-05T12:00:00Z');
 assert.equal(feedFreshness('2026-11-03T18:14:35Z',now).status,'stale');
 assert.equal(feedFreshness('2026-11-05T08:00:00Z',now).status,'fresh');
 assert.equal(feedFreshness(null,now).status,'unknown');
});
test('source provenance is displayed correctly',()=>{
 assert.equal(sourceLabel('state'),'Órgão estadual');
 assert.equal(sourceLabel('federal'),'Órgão federal');
 assert.equal(sourceLabel('municipal'),'Prefeitura / órgão municipal');
 assert.equal(sourceLabel('private'),'Plataforma / leiloeiro privado');
});

test('empty state clearly distinguishes state, day and empty feed',()=>{
 assert.match(emptyResultsMessage({state:'GO',day:'2099-11-04'}),/estado e a data/);
 assert.match(emptyResultsMessage({state:'GO'}),/este estado/);
 assert.match(emptyResultsMessage({day:'2099-11-04'}),/esta data/);
 assert.match(emptyResultsMessage(),/Nenhum próximo leilão/);
});
