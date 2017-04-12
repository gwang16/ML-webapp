# Fetch command line arguments
myArgs <- commandArgs(trailingOnly = TRUE)

# Convert to numerics
nums = as.numeric(myArgs)

# custom function
multiply <- function(nums){
	if (length(nums) == 0){
		return(0)
	}
	else {
		product = 1
		for (i in 1:length(nums)){
			product = product * nums[i]
		}
		return(product)
	}
}


# cat will write the result to the stdout stream
cat(multiply(nums))