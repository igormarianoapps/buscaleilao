import test from 'node:test';
import assert from 'node:assert/strict';
import {groupAuctions,filterAuctions,feedFreshness,sourceLabel,emptyResultsMessage,normalizeSearch} from '../app/agenda.mjs';

const make = (id,state,overrides={}) => ({
  id, state, title:'Leilão', auction_date:'2099-11-03',
  auction_time:'10:00', organizer:'VIP Leilões', source_type:'private',
  status:'scheduled', destination_verified:true, source_link_type:'event', link_verified:true, source_url:'https://www.vipleiloes.com.br/leilao/123',
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

test('calendar-only auctions are excluded from clickable search results',()=>{
 const rows=[
   make('generic','GO',{source_link_type:'calendar',source_url:'https://www.vipleiloes.com.br/agenda'}),
   make('direct','GO',{source_link_type:'event',source_url:'https://www.vipleiloes.com.br/evento/detalhes/123'})
 ];
 assert.deepEqual(filterAuctions(rows,{today:'2099-11-01'}).map(x=>x.id),['direct']);
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

test('date interval is inclusive and accepts either or both bounds',()=>{
 const items=[
  make('first','GO',{auction_date:'2099-11-03'}),
  make('middle','GO',{auction_date:'2099-11-07'}),
  make('last','GO',{auction_date:'2099-11-10'}),
  make('past','GO',{auction_date:'2099-11-01'})];
 assert.deepEqual(filterAuctions(items,{today:'2099-11-03',start:'2099-11-03',end:'2099-11-10'}).map(x=>x.id),['first','middle','last']);
 assert.deepEqual(filterAuctions(items,{today:'2099-11-03',start:'2099-11-07'}).map(x=>x.id),['middle','last']);
 assert.deepEqual(filterAuctions(items,{today:'2099-11-03',end:'2099-11-07'}).map(x=>x.id),['first','middle']);
 assert.deepEqual(filterAuctions(items,{today:'2099-11-03',start:'2099-11-10',end:'2099-11-03'}),[]);
 assert.deepEqual(filterAuctions(items,{today:'2099-11-03',state:'SP'}),[]);
});
test('empty state distinguishes state, period and empty feed',()=>{
 assert.match(emptyResultsMessage({state:'GO',start:'2099-11-03',end:'2099-11-10'}),/estado e o período/);
 assert.match(emptyResultsMessage({state:'GO'}),/este estado/);
 assert.match(emptyResultsMessage({end:'2099-11-04'}),/período selecionado/);
 assert.match(emptyResultsMessage(),/Nenhum próximo leilão/);
});

test('keyword searches title city organizer and id without accents',()=>{
 const items=[make('semob-123','MT',{title:'Leilão de motocicletas',organizer:'Prefeitura de Cuiabá',city:'Cuiabá'}),make('outro','GO',{title:'Carros',city:'Goiânia'})];
 assert.equal(normalizeSearch('  Goiânia  '),'goiania');
 assert.deepEqual(filterAuctions(items,{today:'2099-11-01',keyword:'cuiaba'}).map(a=>a.id),['semob-123']);
 assert.deepEqual(filterAuctions(items,{today:'2099-11-01',keyword:'MOTOCICLETAS'}).map(a=>a.id),['semob-123']);
 assert.deepEqual(filterAuctions(items,{today:'2099-11-01',state:'GO',keyword:'Cuiabá'}),[]);
});
test('unapproved destination never enters the results',()=>{
 assert.deepEqual(filterAuctions([make('notice','GO',{link_verified:false})],{today:'2099-11-01'}),[]);
});

test('keyword searches city, organizer, accents, event id and combines with UF/date',()=>{
 const items=[make('cuiaba-123','MT',{city:'Cuiabá',title:'Leilão Semob',organizer:'Prefeitura de Cuiabá'}),
 make('goiania-456','GO',{city:'Goiânia',title:'Leilão Detran'})];
 assert.deepEqual(filterAuctions(items,{today:'2099-11-01',keyword:'cuiaba',state:'MT'}).map(x=>x.id),['cuiaba-123']);
 assert.deepEqual(filterAuctions(items,{today:'2099-11-01',keyword:'SEMob',state:'GO'}),[]);
 assert.deepEqual(filterAuctions(items,{today:'2099-11-01',keyword:'goiania-456'}).map(x=>x.id),['goiania-456']);
});
test('unverified links and links to news never appear, even on HTTPS',()=>{
 const items=[make('news','MT',{source_link_type:undefined,source_url:'https://prefeitura.gov.br/noticias/leilao'}),
 make('unverified','MT',{link_verified:false}),
 make('with_event_url','MT',{source_link_type:undefined,link_verified:true,event_url:'https://www.focoleiloes.com.br/leilao/497/lotes'})];
 assert.deepEqual(filterAuctions(items,{today:'2099-11-01'}).map(x=>x.id),['with_event_url']);
});

test('per-event approval is required even when the URL shape is trusted',()=>{
 assert.deepEqual(filterAuctions([make('structural','GO',{destination_verified:false})],{today:'2099-11-01'}),[]);
});

test('multiword keyword query finds terms across organizer and city',()=>{
 const items=[make('one','GO',{organizer:'Prefeitura de Goiânia',title:'Leilão de motos'}),
 make('two','SP',{organizer:'VIP Leilões',title:'Carros usados'})];
 assert.deepEqual(filterAuctions(items,{today:'2099-11-01',keyword:'motos goiania'}).map(x=>x.id),['one']);
 assert.deepEqual(filterAuctions(items,{today:'2099-11-01',keyword:'vip sp'}).map(x=>x.id),['two']);
});
