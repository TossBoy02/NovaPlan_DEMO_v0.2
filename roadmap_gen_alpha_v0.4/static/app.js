async function loadRoadmaps(){
  const resp = await fetch('/download');
  const data = await resp.json();
  const out = document.getElementById('output');
  out.innerHTML = '';
  data.roadmaps.forEach(rm => {
    const card = document.createElement('div'); card.className='card';
    card.innerHTML = `<h3>${rm.path_title} — ${rm.focus}</h3><p>Confidence: ${rm.confidence_score}</p>`;
    const ul = document.createElement('ol');
    rm.steps.forEach(s => {
      const li = document.createElement('li');
      li.innerHTML = `<strong>${s.title}</strong> — ${s.objective} <br><em>Duration: ${s.duration_months} months</em><br>Prereqs: ${s.prerequisites.join(', ')}<br>Milestones: ${s.milestones.join(', ')}<br>Resources: ${s.resources.join(', ')}`;
      ul.appendChild(li);
    });
    card.appendChild(ul);
    out.appendChild(card);
  });

  // Build timeline
  const items = new vis.DataSet();
  let id = 1;
  let start = new Date();
  data.roadmaps.forEach((rm, idx) => {
    let cursor = new Date(start);
    rm.steps.forEach((s, i) => {
      const months = s.duration_months || 1;
      const end = new Date(cursor);
      end.setMonth(end.getMonth() + months);
      items.add({id: id++, content: `${rm.focus}: ${s.title}`, start: cursor.toISOString(), end: end.toISOString(), group: idx});
      cursor = new Date(end);
    });
  });
  const container = document.getElementById('timeline');
  const groups = new vis.DataSet(data.roadmaps.map((r,i)=>({id:i, content: r.focus})));
  const options = {stack: false, selectable: true, orientation: 'top'};
  new vis.Timeline(container, items, groups, options);
}

window.onload = loadRoadmaps;
