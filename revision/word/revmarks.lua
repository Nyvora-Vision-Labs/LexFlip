-- Highlight revised text in the Word file.
-- build_rev.py turns every \rev{...} into the markers REVSTARTX / REVENDX.
-- Walking the document top-down, in order, this filter drops the markers and
-- wraps every inline between them in a Span with the character style
-- "Revised", which build_rev.py then gives a yellow highlight.
local on = false

local function process(inlines)
  local out = pandoc.Inlines{}
  local run = pandoc.Inlines{}
  local function flush()
    if #run > 0 then
      out:insert(pandoc.Span(run, {["custom-style"] = "Revised"}))
      run = pandoc.Inlines{}
    end
  end
  for _, el in ipairs(inlines) do
    if el.t == "Str" and (el.text:find("REVSTARTX") or el.text:find("REVENDX")) then
      local s = el.text
      while #s > 0 do
        local a = s:find("REVSTARTX", 1, true)
        local b = s:find("REVENDX", 1, true)
        local i, tag
        if a and (not b or a < b) then i, tag = a, "start"
        elseif b then i, tag = b, "end" end
        if not i then
          if on then run:insert(pandoc.Str(s)) else out:insert(pandoc.Str(s)) end
          s = ""
        else
          local before = s:sub(1, i - 1)
          if #before > 0 then
            if on then run:insert(pandoc.Str(before)) else out:insert(pandoc.Str(before)) end
          end
          if tag == "start" then on = true; s = s:sub(i + 9)
          else flush(); on = false; s = s:sub(i + 7) end
        end
      end
    else
      if on then run:insert(el) else out:insert(el) end
    end
  end
  flush()
  return out
end

return {{
  traverse = "topdown",
  -- returning false stops pandoc from descending into the spans just made,
  -- which would otherwise be wrapped again without end
  Inlines = function(inl) return process(inl), false end,
}}
