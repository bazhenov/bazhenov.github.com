module Jekyll
	module Filters
		def summarize(str, splitstr = /<!--\s*excerpt\s*-->/i)
			str.split(splitstr)[0]
		end
	end
end
