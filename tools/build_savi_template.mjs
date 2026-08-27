import fs from 'node:fs/promises';
import { SpreadsheetFile, Workbook } from '@oai/artifact-tool';

const out = 'outputs/Plantilla_Base_Comparables_SAVI.xlsx';
await fs.mkdir('outputs', { recursive: true });
const wb = Workbook.create();
const comp = wb.worksheets.add('Comparables');
const cat = wb.worksheets.add('Catalogos');
const guide = wb.worksheets.add('Instrucciones');
for (const s of [comp, cat, guide]) s.showGridLines = false;

const headers = ['ID comparable','Operación','Tipo inmueble','Zona normalizada','Municipio','Latitud','Longitud','Dirección / referencia','Precio anunciado MXN','Moneda origen','Terreno m²','Construcción m²','Recámaras','Baños','Estacionamientos','Antigüedad años','Conservación','Calidad','Fuente','URL origen','Fecha observación','Verificado','Activo','Precio por m²','Estatus de calidad','Notas'];
comp.getRange('A1:Z1').values = [headers];
comp.getRange('A1:Z1').format = {fill:'#06285A',font:{bold:true,color:'#FFFFFF'},wrapText:true,horizontalAlignment:'center'};
comp.getRange('A2:Z2').values = [['CMP-0001','VENTA','CASA','Lomas del Tecnológico','San Luis Potosí',22.1508,-100.9842,'Ejemplo: no usar como dato real',3900000,'MXN',160,180,3,2,2,5,'BUENO','MEDIA','Ejemplo','',new Date('2026-08-01'),false,true,null,null,'Reemplace esta fila por comparables verificados']];
for(let r=2;r<=201;r++) {
  comp.getRange(`X${r}`).formulas = [[`=IFERROR(I${r}/IF(L${r}>0,L${r},K${r}),"")`]];
  comp.getRange(`Y${r}`).formulas = [[`=IF(OR(B${r}="",C${r}="",D${r}="",I${r}<=0,AND(K${r}<=0,L${r}<=0)),"INCOMPLETO",IF(W${r}=FALSE,"INACTIVO",IF(V${r}=FALSE,"PENDIENTE VALIDAR","LISTO")))`]];
}
comp.getRange('F2:G201').format.numberFormat = '0.000000';
comp.getRange('I2:I201').format.numberFormat = '"$"#,##0';
comp.getRange('K2:L201').format.numberFormat = '#,##0.00';
comp.getRange('U2:U201').format.numberFormat = 'yyyy-mm-dd';
comp.getRange('X2:X201').format.numberFormat = '"$"#,##0.00';
comp.getRange('A1:Z201').format.borders = {preset:'inside',style:'thin',color:'#D9E4F2'};
comp.getRange('A1:Z1').format.rowHeight = 34;
comp.getRange('A:Z').format.columnWidth = 14;
comp.getRange('D:D').format.columnWidth = 22; comp.getRange('H:H').format.columnWidth = 32; comp.getRange('T:T').format.columnWidth = 32; comp.getRange('Z:Z').format.columnWidth = 36;
comp.freezePanes.freezeRows(1);
comp.getRange('B2:B201').dataValidation = {rule:{type:'list',values:['VENTA','RENTA']}};
comp.getRange('C2:C201').dataValidation = {rule:{type:'list',values:['CASA','DEPARTAMENTO','BODEGA','TERRENO']}};
comp.getRange('Q2:Q201').dataValidation = {rule:{type:'list',values:['MALO','REGULAR','BUENO','MUY_BUENO','EXCELENTE']}};
comp.getRange('R2:R201').dataValidation = {rule:{type:'list',values:['BASICA','MEDIA','BUENA','ALTA']}};
comp.getRange('V2:W201').dataValidation = {rule:{type:'list',values:['TRUE','FALSE']}};
comp.getRange('Y2:Y201').conditionalFormats.add('containsText',{text:'LISTO',format:{fill:'#DCFCE7',font:{color:'#166534'}}});
comp.getRange('Y2:Y201').conditionalFormats.add('containsText',{text:'INCOMPLETO',format:{fill:'#FEE2E2',font:{color:'#991B1B'}}});

cat.getRange('A1:D1').values = [['Campo','Valores permitidos','Uso en SAVI','Regla']];
cat.getRange('A2:D8').values = [
 ['Operación','VENTA / RENTA','Segmentación','No mezclar mercados'],['Tipo inmueble','CASA / DEPARTAMENTO / BODEGA / TERRENO','Segmentación','No mezclar tipos'],['Conservación','MALO a EXCELENTE','Factor Fc','Captura obligatoria'],['Verificado','TRUE / FALSE','Confianza','Preferir TRUE'],['Activo','TRUE / FALSE','IQR y selección','FALSE excluye del modelo'],['Construcción m²','Número mayor a cero','Precio por m²','Si no existe, usar terreno m²'],['Zona normalizada','Catálogo propio de colonias','Geo-matching','Evitar sinónimos']];
cat.getRange('A1:D1').format = {fill:'#0B5ED7',font:{bold:true,color:'#FFFFFF'}}; cat.getRange('A1:D8').format.borders={preset:'inside',style:'thin',color:'#D9E4F2'}; cat.getRange('A:D').format.columnWidth=28;

guide.getRange('A1:H1').merge(); guide.getRange('A1').values=[['SAVI · Plantilla de comparables para homologación']]; guide.getRange('A1:H1').format={fill:'#06285A',font:{bold:true,color:'#FFFFFF',size:16},horizontalAlignment:'center'};
guide.getRange('A3:B9').values = [['1. Captura','Registre un inmueble por fila; no agregue solicitudes de compra.'],['2. Normalización','Use una sola denominación por colonia o zona.'],['3. Validación','Marque Verificado cuando tenga fuente y fecha revisadas.'],['4. IQR','Con 10 o más datos activos del mismo segmento, revise extremos de $/m².'],['5. Homologación','El sistema aplica Fnegociación, Fsuperficie, Fconservación y Fedad.'],['6. Alcance','La salida es Opinión de Valor Digital, no avalúo formal.'],['Fuente técnica','Metodología comparable sujeta a revisión profesional y reglas SHF aplicables.']];
guide.getRange('A3:A9').format={fill:'#EAF3FF',font:{bold:true,color:'#06285A'}}; guide.getRange('A3:B9').format={wrapText:true}; guide.getRange('A:B').format.columnWidth=50; guide.getRange('A3:B9').format.rowHeight=34;
const xlsx = await SpreadsheetFile.exportXlsx(wb); await xlsx.save(out);
const preview = await wb.render({sheetName:'Comparables',range:'A1:Z12',scale:1,format:'png'});
await fs.writeFile('outputs/Plantilla_Base_Comparables_SAVI_preview.png', new Uint8Array(await preview.arrayBuffer()));
