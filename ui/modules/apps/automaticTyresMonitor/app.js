(function () {
  'use strict';
  angular.module('beamng.apps').directive('automaticTyresMonitor', ['$interval', function ($interval) {
    return {restrict:'EA',replace:true,templateUrl:'/ui/modules/apps/automaticTyresMonitor/app.html',link:function(scope,element){
      var streams=['TyreWearThermals','AutomaticTyresTelemetry'];
      var thermal={},telemetry={},thermalTime=0,telemetryTime=0;
      var positions=['FL','FR','RL','RR'];
      var labels={FL:'Front left',FR:'Front right',RL:'Rear left',RR:'Rear right',RL2:'Rear left, axle 2',RR2:'Rear right, axle 2'};
      function numeric(n){return typeof n==='number'&&isFinite(n)?n:null;}
      function mean(values){var a=values.filter(function(x){return x!==null;});return a.length?a.reduce(function(x,y){return x+y;},0)/a.length:null;}
      function blank(name){return {name:name,label:labels[name]||name,temps:[null,null,null],average:null,pressure:null,condition:null,camber:null,contactBias:null,brake:null,placeholder:true,status:{tone:'neutral'}};}
      scope.selected=null;scope.live=false;scope.hasWear=false;scope.wheels=[];scope.displayWheels=positions.map(blank);
      // Measure the app itself: the game viewport does not change when a UI app resizes.
      var host=element[0],lastWidth=0,lastHeight=0,resizeObserver;
      function resize(){
        var width=host.clientWidth,height=host.clientHeight;
        if(!width||!height||(width===lastWidth&&height===lastHeight))return;
        lastWidth=width;lastHeight=height;
        var compact=width<230||height<270;
        var scale=Math.max(.6,Math.min(2.5,(width-16)/200,(height-16)/228));
        host.classList.toggle('tdash-compact',compact);
        host.classList.toggle('tdash-large',!compact&&scale>=1.3);
        host.style.setProperty('--td-scale',scale.toFixed(4));
      }
      if(typeof ResizeObserver!=='undefined'){
        resizeObserver=new ResizeObserver(resize);resizeObserver.observe(host);
      }
      resize();
      scope.$on('app:resized',resize);
      try{scope.tempUnit=localStorage.getItem('automaticTyres.tempUnit')==='°F'?'°F':'°C';scope.pressureUnit=localStorage.getItem('automaticTyres.pressureUnit')==='kPa'?'kPa':'PSI';}catch(e){scope.tempUnit='°C';scope.pressureUnit='PSI';}
      scope.number=function(n,d){return numeric(n)===null?'—':n.toFixed(d);};
      scope.temperature=function(n){return numeric(n)===null?'—':Math.round(scope.tempUnit==='°F'?n*1.8+32:n);};
      scope.pressure=function(n){return numeric(n)===null?'—':(scope.pressureUnit==='kPa'?n*6.894757:n).toFixed(scope.pressureUnit==='kPa'?0:1);};
      scope.toggleTemperature=function(){scope.tempUnit=scope.tempUnit==='°C'?'°F':'°C';try{localStorage.setItem('automaticTyres.tempUnit',scope.tempUnit);}catch(e){}};
      scope.togglePressure=function(){scope.pressureUnit=scope.pressureUnit==='PSI'?'kPa':'PSI';try{localStorage.setItem('automaticTyres.pressureUnit',scope.pressureUnit);}catch(e){}};
      scope.zoneColor=function(t,target){if(numeric(t)===null||!(target>0))return '#353b40';var r=t/target;return r<.85?'#20bda5':r<=1.15?'#43bd64':r<1.35?'#b1bf37':'#cd6847';};
      scope.brakeColor=function(w){var r=w.brake/(w.brakeTarget>0?w.brakeTarget:800);return r<.5?'#32a6c6':r<.85?'#43bd64':r<1?'#b1bf37':'#cd6847';};
      scope.lifeHeight=function(w){return scope.live&&w.condition!==null?w.condition+'%':'100%';};
      scope.contactPosition=function(w){return (50+w.contactBias*45)+'%';};
      scope.contactLabel=function(w){
        if(w.contactBias===null)return '—';if(Math.abs(w.contactBias)<=.15)return 'CENTRE';
        var side=/L(?:\d+)?$/.test(w.name)?'L':/R(?:\d+)?$/.test(w.name)?'R':null;
        return side?((w.contactBias>0)===(side==='L')?'INNER':'OUTER'):(w.contactBias>0?'RIGHT':'LEFT');
      };
      scope.tyreTitle=function(w){return w.label+'; tread '+scope.temperature(w.average)+scope.tempUnit+'; '+(scope.live&&w.condition!==null?scope.number(w.condition,0)+'% life remaining':'wear unavailable')+'; tap for details';};
      function status(w){
        if(w.deflated)return {tone:'danger',label:'FLAT'};
        if(w.pressure!==null&&w.targetPressure>0&&w.pressure<w.targetPressure*.7)return {tone:'warm',label:'LOW PSI'};
        if(w.average!==null&&w.target>0)return {tone:w.average/w.target>1.35?'hot':'normal'};
        return {tone:'neutral'};
      }
      function rank(name){var i=positions.indexOf(name);return i<0?100:i;}
      function build(){
        var now=Date.now(),tf=now-thermalTime<1800,vf=now-telemetryTime<1800;
        if(!tf&&!vf){scope.live=false;scope.hasWear=false;resize();return;}
        var names={};Object.keys(tf?thermal:{}).forEach(function(n){names[n]=true;});Object.keys(vf?telemetry:{}).forEach(function(n){names[n]=true;});
        var selected=scope.selected&&scope.selected.name;
        scope.wheels=Object.keys(names).sort(function(a,b){return rank(a)-rank(b)||a.localeCompare(b);}).map(function(name){
          var t=tf?thermal[name]||{}:{},v=vf?telemetry[name]||{}:{};
          var temperatures=[0,1,2].map(function(i){return numeric((t.temp||[])[i]);});
          var condition=numeric(t.condition);if(condition!==null)condition=Math.max(0,Math.min(100,condition));
          var bias=numeric(t.load_bias);if(bias!==null)bias=Math.max(-1,Math.min(1,bias));
          var w={name:name,label:labels[name]||name,temps:temperatures,average:numeric(t.avg_temp),target:numeric(t.working_temp),core:numeric((t.temp||[])[3]),condition:condition,camber:numeric(t.camber),contactBias:bias,
            pressure:numeric(v.pressurePsi),targetPressure:numeric(v.targetPressurePsi),sideSlip:numeric(v.sideSlipMps),brake:numeric(t.brake_temp),brakeTarget:numeric(t.brake_working_temp),deflated:v.deflated===true};
          if(w.average===null)w.average=mean(temperatures);w.status=status(w);return w;
        });
        scope.live=scope.wheels.length>0;
        scope.hasWear=scope.wheels.some(function(w){return w.condition!==null;});
        var standard=scope.wheels.some(function(w){return positions.indexOf(w.name)>=0;});
        scope.displayWheels=scope.live?(standard?positions.map(function(name){return scope.wheels.find(function(w){return w.name===name;})||blank(name);}).concat(scope.wheels.filter(function(w){return positions.indexOf(w.name)<0;})):scope.wheels):positions.map(blank);
        scope.selected=scope.wheels.find(function(w){return w.name===selected;})||null;
        resize();
      }
      scope.select=function(w){if(!w.placeholder)scope.selected=w;};
      scope.back=function(){scope.selected=null;};
      function clear(){thermal={};telemetry={};thermalTime=0;telemetryTime=0;scope.wheels=[];scope.displayWheels=positions.map(blank);scope.selected=null;scope.live=false;scope.hasWear=false;resize();}
      StreamsManager.add(streams);
      scope.$on('streamsUpdate',function(event,values){
        if(values.TyreWearThermals){thermal={};(values.TyreWearThermals.data||[]).forEach(function(w){if(w.name)thermal[w.name]=w;});thermalTime=Date.now();}
        if(values.AutomaticTyresTelemetry){telemetry={};(values.AutomaticTyresTelemetry.data||[]).forEach(function(w){if(w.name)telemetry[w.name]=w;});telemetryTime=Date.now();}
        build();
      });
      scope.$on('VehicleFocusChanged',clear);scope.$on('VehicleReset',clear);
      // Also provides a resize fallback for older game browser runtimes.
      var clock=$interval(function(){build();resize();},500);
      scope.$on('$destroy',function(){StreamsManager.remove(streams);$interval.cancel(clock);if(resizeObserver)resizeObserver.disconnect();});
    }};
  }]);
})();
