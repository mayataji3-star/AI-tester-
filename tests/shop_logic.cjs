// Direct tests of the shop's real JS; not a substitute for browser testing.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('shop/index.html','utf8');
const source=html.match(/<script>([\s\S]*)<\/script>/)[1];
const elements={};
for(const id of ['search','products','empty','cart','total','message','checkout'])elements['#'+id]={value:'',innerHTML:'',textContent:'',hidden:false,events:{},addEventListener(event,fn){this.events[event]=fn;}};
const context={document:{querySelector:s=>elements[s]}};vm.createContext(context);vm.runInContext(source,context);
const call=s=>vm.runInContext(s,context);
elements['#search'].value=' HEAD ';call('renderProducts()');
assert(elements['#products'].innerHTML.includes('Headphones'));assert(!elements['#products'].innerHTML.includes('Keyboard'));
elements['#search'].value='zzzz';call('renderProducts()');assert.equal(elements['#empty'].hidden,false);
call("add('headphones');add('headphones');add('mouse')");assert.equal(elements['#total'].textContent,'Total: £50.00');
call("quantity('headphones',{value:'3'})");assert.equal(elements['#total'].textContent,'Total: £70.00');
for(const q of ['0','-1','1.5','100']){call(`quantity('headphones',{value:'${q}'})`);assert.equal(elements['#total'].textContent,'Total: £70.00');}
call("remove('mouse')");assert.equal(elements['#total'].textContent,'Total: £60.00');
elements['#checkout'].events.submit({preventDefault(){}});assert.equal(elements['#total'].textContent,'Total: £0.00');assert(elements['#message'].textContent.startsWith('Demo order placed'));
elements['#checkout'].events.submit({preventDefault(){}});assert.equal(elements['#message'].textContent,'Your cart is empty.');
console.log('Shop JS checks passed: search, quantities, totals, remove, checkout state. Native email validation not tested.');
