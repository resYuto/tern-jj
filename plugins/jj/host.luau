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
		local kind = string.match(line.text, "^([AMD]) ")
		local tone = if kind == "A" then "success" elseif kind == "D" then "error" elseif kind == "M" then "warn" else nil
		table.insert(lines, ui.text({ ui.span(line.text, tone) }))
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
