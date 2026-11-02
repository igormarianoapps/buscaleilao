import test from 'node:test';
import assert from 'node:assert/strict';
import {groupAuctions,filterAuctions} from '../app/agenda.mjs';

const make = (id,state,overrides={}) => ({
  id, state, title:'Leilão', auction_date:'2099-11-03',
  auction_time:'10:00', organizer:'VIP Leilões', source_type:'private',
  status:'scheduled', source_url:'https://www.vipleiloes.com.br/agenda',
  ...overrides
});

test('VIP multi-state event is one result with searchable states',()=>{
  const items=[
    make('vip-2099-11-03-1000-go-financeiras','GO'),
    make('vip-2099-11-03-1000-sp-financeiras','SP'),
    make('vip-2099-11-03-1000-mg-financeiras','MG')
  ];
  assert.equal(groupAuctions(items).length,1);
  assert.deepEqual(groupAuctions(items)[0].states,['GO','MG','SP']);
  assert.equal(filterAuctions(items,{state:'SP',today:'2099-11-01'}).length,1);
  assert.equal(filterAuctions(items,{state:'RJ',today:'2099-11-01'}).length,0);
});

test('different platforms and dates stay separate',()=>{
  const items=[
    make('vip-2099-11-03-1000-sp-financeiras','SP'),
    make('vip-2099-11-04-1000-sp-financeiras','SP',{auction_date:'2099-11-04'}),
    make('copart-2099-11-03-sp-osasco','SP',{organizer:'Copart'})
  ];
  assert.equal(groupAuctions(items).length,3);
});

test('date and status filters exclude expired and cancelled',()=>{
  const items=[
    make('vip-2099-11-03-1000-sp-financeiras','SP'),
    make('old','GO',{auction_date:'2020-01-01'}),
    make('cancelled','SP',{status:'cancelled'})
  ];
  assert.equal(filterAuctions(items,{today:'2099-11-01',day:'2099-11-03'}).length,1);
  assert.equal(filterAuctions(items,{today:'2100-01-01'}).length,0);
});
