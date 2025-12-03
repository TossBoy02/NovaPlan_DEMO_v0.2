import { useState } from "react";
import questions from "./data/questions.json";

function App() {
	const [loading, setLoading] = useState(false);
	const [result, setResult] = useState(null);
	const [error, setError] = useState("");

	const handleSubmit = async (e) => {
		e.preventDefault();
		setError("");
		setLoading(true);
		setResult(null);
		const formData = new FormData(e.currentTarget);
		const answers = questions.map((q) => ({
			questionId: q.id,
			type: formData.get(`question-${q.id}`),
		}));
		const summary = formData.get("summary") || "";
		try {
			const res = await fetch("http://localhost:8000/generate", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ answers, summary }),
			});
			if (!res.ok) throw new Error("Failed to generate roadmaps");
			const data = await res.json();
			setResult(data);
		} catch (err) {
			setError(err.message || "Something went wrong");
		} finally {
			setLoading(false);
		}
	};

	return (
		<main>
			<h1 className="title">Welcome to NovaPlan!</h1>
			<form onSubmit={handleSubmit}>
				{questions.map((question) => (
					<div className="group" key={question.id}>
						<p>{question.question}</p>
						<ul>
							{question.options.map((opt, idx) => (
								<li key={idx}>
									<input
										type="radio"
										name={`question-${question.id}`}
										id={`${question.id}-${idx}`}
										value={opt.type}
										required={idx === 0}
									/>
									<label htmlFor={`${question.id}-${idx}`}>{opt.text}</label>
								</li>
							))}
						</ul>
					</div>
				))}
				<div className="summary-info">
					<p>Write a brief summary about yourself :</p>
					<textarea name="summary" placeholder="Talk about yourself" />
				</div>
				<button type="submit" disabled={loading}>
					{loading ? "Generating..." : "Submit"}
				</button>
			</form>

			{error && <p style={{ color: "red" }}>{error}</p>}

			{result && (
				<section>
					<h2>Suggested career: {result.chosen_career}</h2>
					
					{/* Tree Visualizations */}
					{result.images && result.images.length > 0 && (
						<div style={{ marginBottom: "2rem" }}>
							<h3>Roadmap Visualizations (Top-Down Tree Structure)</h3>
							<div style={{ display: "grid", gap: 24, gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))" }}>
								{result.images.map((src, i) => (
									<div key={i} style={{ border: "1px solid #e5e7eb", borderRadius: "8px", padding: "16px", backgroundColor: "#f9fafb" }}>
										<h4 style={{ marginTop: 0, color: "#374151" }}>
											{result.roadmaps[i]?.path_title} — {result.roadmaps[i]?.focus}
										</h4>
										<img 
											src={`http://localhost:8000${src}`} 
											alt={`Roadmap ${i + 1}`} 
											style={{ 
												width: "100%", 
												height: "auto",
												borderRadius: "4px",
												boxShadow: "0 2px 4px rgba(0,0,0,0.1)"
											}} 
										/>
									</div>
								))}
							</div>
						</div>
					)}

					{/* Detailed Roadmap Breakdown with Milestones */}
					<div style={{ marginTop: "2rem" }}>
						<h3>Detailed Roadmap Breakdown</h3>
						{result.roadmaps?.map((r, i) => (
							<div key={i} style={{ 
								marginBottom: "2rem", 
								padding: "20px", 
								border: "1px solid #d1d5db", 
								borderRadius: "8px",
								backgroundColor: "#ffffff"
							}}>
								<h4 style={{ marginTop: 0, color: "#1f2937" }}>
									{r.path_title} — {r.focus} (Confidence: {Math.round(r.confidence_score * 100)}%)
								</h4>
								
								{/* Render hierarchical steps with milestones */}
								<div style={{ marginLeft: "20px" }}>
									{r.steps.map((step, stepIndex) => (
										<div key={stepIndex} style={{ marginBottom: "16px" }}>
											<div style={{ 
												fontWeight: "bold", 
												fontSize: "16px", 
												color: "#374151",
												marginBottom: "8px"
											}}>
												{stepIndex + 1}. {step.title}
											</div>
											<div style={{ 
												fontSize: "14px", 
												color: "#6b7280", 
												marginBottom: "8px",
												fontStyle: "italic"
											}}>
												{step.objective}
											</div>
											<div style={{ fontSize: "13px", color: "#9ca3af", marginBottom: "8px" }}>
												Duration: {step.duration_months} month{step.duration_months !== 1 ? 's' : ''}
											</div>
											
											{/* Milestones */}
											{step.milestones && step.milestones.length > 0 && (
												<div style={{ marginLeft: "16px", marginBottom: "8px" }}>
													<div style={{ fontWeight: "600", fontSize: "13px", color: "#059669", marginBottom: "4px" }}>
														Milestones:
													</div>
													<ul style={{ margin: 0, paddingLeft: "16px" }}>
														{step.milestones.map((milestone, mIndex) => (
															<li key={mIndex} style={{ fontSize: "13px", color: "#374151" }}>
																{milestone}
															</li>
														))}
													</ul>
												</div>
											)}

											{/* Prerequisites */}
											{step.prerequisites && step.prerequisites.length > 0 && (
												<div style={{ marginLeft: "16px", marginBottom: "8px" }}>
													<div style={{ fontWeight: "600", fontSize: "13px", color: "#dc2626", marginBottom: "4px" }}>
														Prerequisites:
													</div>
													<div style={{ fontSize: "13px", color: "#6b7280" }}>
														{step.prerequisites.join(", ")}
													</div>
												</div>
											)}

											{/* Tasks */}
											{step.tasks && step.tasks.length > 0 && (
												<div style={{ marginLeft: "16px", marginBottom: "8px" }}>
													<div style={{ fontWeight: "600", fontSize: "13px", color: "#7c3aed", marginBottom: "4px" }}>
														Specific Tasks:
													</div>
													<ol style={{ margin: 0, paddingLeft: "16px" }}>
														{step.tasks.map((task, tIndex) => (
															<li key={tIndex} style={{ fontSize: "13px", color: "#374151", marginBottom: "2px" }}>
																{task}
															</li>
														))}
													</ol>
												</div>
											)}

											{/* Child Steps (Branching) */}
											{step.children && step.children.length > 0 && (
												<div style={{ marginLeft: "20px", marginTop: "12px" }}>
													<div style={{ fontWeight: "600", fontSize: "14px", color: "#7c3aed", marginBottom: "8px" }}>
														Sub-steps:
													</div>
													{step.children.map((child, childIndex) => (
														<div key={childIndex} style={{ 
															marginBottom: "12px", 
															padding: "12px", 
															borderLeft: "3px solid #e5e7eb",
															backgroundColor: "#f8fafc"
														}}>
															<div style={{ fontWeight: "600", fontSize: "14px", color: "#374151", marginBottom: "4px" }}>
																{child.title}
															</div>
															<div style={{ fontSize: "13px", color: "#6b7280", marginBottom: "4px" }}>
																{child.objective}
															</div>
															<div style={{ fontSize: "12px", color: "#9ca3af", marginBottom: "6px" }}>
																Duration: {child.duration_months} month{child.duration_months !== 1 ? 's' : ''}
															</div>
															{child.milestones && child.milestones.length > 0 && (
																<div style={{ marginLeft: "8px" }}>
																	<div style={{ fontWeight: "600", fontSize: "12px", color: "#059669", marginBottom: "2px" }}>
																		Milestones:
																	</div>
																	<ul style={{ margin: 0, paddingLeft: "12px" }}>
																		{child.milestones.map((milestone, mIndex) => (
																			<li key={mIndex} style={{ fontSize: "12px", color: "#374151" }}>
																				{milestone}
																			</li>
																		))}
																	</ul>
																</div>
															)}
															{child.tasks && child.tasks.length > 0 && (
																<div style={{ marginLeft: "8px" }}>
																	<div style={{ fontWeight: "600", fontSize: "12px", color: "#7c3aed", marginBottom: "2px" }}>
																		Tasks:
																	</div>
																	<ol style={{ margin: 0, paddingLeft: "12px" }}>
																		{child.tasks.map((task, tIndex) => (
																			<li key={tIndex} style={{ fontSize: "12px", color: "#374151", marginBottom: "1px" }}>
																				{task}
																			</li>
																		))}
																	</ol>
																</div>
															)}
														</div>
													))}
												</div>
											)}
										</div>
									))}
								</div>
							</div>
						))}
					</div>

					<div style={{ marginTop: "2rem", textAlign: "center" }}>
						<a 
							href="http://localhost:8000/download" 
							target="_blank" 
							rel="noreferrer"
							style={{
								display: "inline-block",
								padding: "12px 24px",
								backgroundColor: "#3b82f6",
								color: "white",
								textDecoration: "none",
								borderRadius: "6px",
								fontWeight: "600"
							}}
						>
							Download Complete Roadmap JSON
						</a>
					</div>
				</section>
			)}
		</main>
	);
}

export default App;
