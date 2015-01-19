module Jekyll
	module Filters
		def rewrite_local_links(str, global_url)
			str.gsub(/"(\/.[^"]+)"/, "\"#{global_url}\\1\"")
		end
	end
end
