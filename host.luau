--!strict

local ui = tern.ui

tern.on("spawn", function(spec: SpawnSpec): SpawnSpec
	spec.env.JJ_PAGER = "cat"
	return spec
end)

type State = {
	lines: { Node }?,
	status: number?,
}

local status: LensDef<State> = {
	open = function(_run, _cx)
		return { lines = {}, status = nil }
	end,
	line = function(state, line)
		local lines = state.lines
		if not lines then
			return
		end
		if #lines == 5000 then
			state.lines = nil -- Large output stays raw rather than being truncated.
			return
		end
		local text = line.text
		local kind = string.match(text, "^([AMDR]) ")
		local tone = if kind == "A" then "success" elseif kind == "D" then "error" elseif kind then "warning" else nil
		local label, change, commit, rest = string.match(text, "^(Working copy%s+%(@%)%s*:%s*)(%l+)(%s+%x+)(.*)$")
		if not label then
			label, change, commit, rest = string.match(text, "^(Parent commit %(@%-%)%s*:%s*)(%l+)(%s+%x+)(.*)$")
		end
		if label and change and commit and rest then
			table.insert(lines, ui.text({
				ui.span(label, "muted"),
				ui.span(change, "accent"),
				ui.span(commit, "info"),
				ui.span(rest),
			}))
		else
			if text == "The working copy has no changes." then
				tone = "success"
			elseif text == "Working copy changes:" then
				tone = "strong"
			end
			table.insert(lines, ui.text({ ui.span(text, tone) }))
		end
	end,
	finish = function(state, code)
		state.status = code
	end,
	view = function(state)
		local lines = state.lines
		if state.status ~= 0 or not lines or #lines == 0 then
			return nil
		end
		return ui.card("Jujutsu status", { ui.lines(lines) })
	end,
}

tern.lens.define("status", status)
