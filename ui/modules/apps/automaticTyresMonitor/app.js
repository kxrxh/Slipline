(function () {
  'use strict';
  angular.module('beamng.apps').directive('automaticTyresMonitor', ['$interval', function ($interval) {
    return {restrict:'EA',replace:true,templateUrl:'/ui/modules/apps/automaticTyresMonitor/app.html',link:function(scope){
      var streams=['TyreWearThermals','AutomaticTyresTelemetry'];
      var thermal={},telemetry={},thermalTime=0,telemetryTime=0;
      var positions=['FL','FR','RL','RR'];
      var labels={FL:'Front left',FR:'Front right',RL:'Rear left',RR:'Rear right',RL2:'Rear left, axle 2',RR2:'Rear right, axle 2'};
      function numeric(n){return typeof n==='number'&&isFinite(n)?n:null;}
      function mean(values){var a=values.filter(function(x){return x!==null;});return a.length?a.reduce(function(x,y){return x+y;},0)/a.length:null;}
      function blank(name){return {name:name,label:labels[name]||name,temps:[null,null,null],average:null,pressure:null,placeholder:true,status:{tone:'neutral'}};}
      scope.selected=null;scope.live=false;scope.wheels=[];scope.displayWheels=positions.map(blank);
      try{scope.tempUnit=localStorage.getItem('automaticTyres.tempUnit')==='°F'?'°F':'°C';scope.pressureUnit=localStorage.getItem('automaticTyres.pressureUnit')==='kPa'?'kPa':'PSI';}catch(e){scope.tempUnit='°C';scope.pressureUnit='PSI';}
      scope.number=function(n,d){return numeric(n)===null?'—':n.toFixed(d);};
      scope.temperature=function(n){return numeric(n)===null?'—':Math.round(scope.tempUnit==='°F'?n*1.8+32:n);};
      scope.pressure=function(n){return numeric(n)===null?'—':(scope.pressureUnit==='kPa'?n*6.894757:n).toFixed(scope.pressureUnit==='kPa'?0:1);};
      scope.toggleTemperature=function(){scope.tempUnit=scope.tempUnit==='°C'?'°F':'°C';try{localStorage.setItem('automaticTyres.tempUnit',scope.tempUnit);}catch(e){}};
      scope.togglePressure=function(){scope.pressureUnit=scope.pressureUnit==='PSI'?'kPa':'PSI';try{localStorage.setItem('automaticTyres.pressureUnit',scope.pressureUnit);}catch(e){}};
      scope.zoneColor=function(t,target){if(numeric(t)===null||!target)return '#353b40';var r=t/target;return r<.85?'#397393':r<=1.15?'#519072':r<1.35?'#bd8a43':'#c36050';};
      function status(w){
        if(w.deflated)return {tone:'danger',label:'FLAT'};
        if(w.pressure!==null&&w.targetPressure>0&&w.pressure<w.targetPressure*.7)return {tone:'warm',label:'LOW PSI'};
        if(w.average!==null&&w.target>0)return {tone:w.average/w.target>1.35?'hot':'normal'};
        return {tone:'neutral'};
      }
      function rank(name){var i=positions.indexOf(name);return i<0?100:i;}
      function build(){
        var now=Date.now(),tf=now-thermalTime<1800,vf=now-telemetryTime<1800;
        if(!tf&&!vf){scope.live=false;return;}
        var names={};Object.keys(tf?thermal:{}).forEach(function(n){names[n]=true;});Object.keys(vf?telemetry:{}).forEach(function(n){names[n]=true;});
        var selected=scope.selected&&scope.selected.name;
        scope.wheels=Object.keys(names).sort(function(a,b){return rank(a)-rank(b)||a.localeCompare(b);}).map(function(name){
          var t=tf?thermal[name]||{}:{},v=vf?telemetry[name]||{}:{};
          var temperatures=[0,1,2].map(function(i){return numeric((t.temp||[])[i]);});
          var condition=numeric(t.condition);if(condition!==null)condition=Math.max(0,Math.min(100,condition));
          var w={name:name,label:labels[name]||name,temps:temperatures,average:numeric(t.avg_temp),target:numeric(t.working_temp),core:numeric((t.temp||[])[3]),condition:condition,
            pressure:numeric(v.pressurePsi),targetPressure:numeric(v.targetPressurePsi),sideSlip:numeric(v.sideSlipMps),brake:numeric(t.brake_temp),deflated:v.deflated===true};
          if(w.average===null)w.average=mean(temperatures);w.status=status(w);return w;
        });
        scope.live=scope.wheels.length>0;
        scope.displayWheels=scope.live?scope.wheels:positions.map(blank);
        scope.selected=scope.wheels.find(function(w){return w.name===selected;})||null;
      }
      scope.select=function(w){if(!w.placeholder)scope.selected=w;};
      function clear(){thermal={};telemetry={};thermalTime=0;telemetryTime=0;scope.wheels=[];scope.displayWheels=positions.map(blank);scope.selected=null;scope.live=false;}
      StreamsManager.add(streams);
      scope.$on('streamsUpdate',function(event,values){
        if(values.TyreWearThermals){thermal={};(values.TyreWearThermals.data||[]).forEach(function(w){if(w.name)thermal[w.name]=w;});thermalTime=Date.now();}
        if(values.AutomaticTyresTelemetry){telemetry={};(values.AutomaticTyresTelemetry.data||[]).forEach(function(w){if(w.name)telemetry[w.name]=w;});telemetryTime=Date.now();}
        build();
      });
      scope.$on('VehicleFocusChanged',clear);scope.$on('VehicleReset',clear);
      var clock=$interval(build,500);
      scope.$on('$destroy',function(){StreamsManager.remove(streams);$interval.cancel(clock);});
    }};
  }]);
})();
